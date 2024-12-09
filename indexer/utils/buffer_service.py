#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/11/19 下午6:07
Author  : xuzh
Project : hemera_indexer
"""
import logging
import os
import signal
import threading
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, Thread
from typing import Callable, Dict

from common.utils.exception_control import get_exception_details

BUFFER_BLOCK_SIZE = os.environ.get("BUFFER_BLOCK_SIZE", 1)
BUFFER_LINGER_MS = os.environ.get("BUFFER_LINGER_MS", 5000)
MAX_BUFFER_SIZE = os.environ.get("MAX_BUFFER_SIZE", 1)
ASYNC_SUBMIT = os.environ.get("ASYNC_SUBMIT", False)
CONCURRENT_SUBMITTERS = os.environ.get("CONCURRENT_SUBMITTERS", 1)
CRASH_INSTANTLY = os.environ.get("CRASH_INSTANTLY", True)


class BufferService:

    def __init__(
        self,
        item_exporters,
        required_output_types,
        block_size: int = BUFFER_BLOCK_SIZE,
        linger_ms: int = BUFFER_LINGER_MS,
        max_buffer_size: int = MAX_BUFFER_SIZE,
        export_workers: int = CONCURRENT_SUBMITTERS,
        success_callback: Callable = None,
        exception_callback: Callable = None,
    ):
        self.block_size = block_size
        self.linger_ms = linger_ms
        self.max_buffer_size = max_buffer_size

        self.item_exporters = item_exporters
        self.required_output_types = required_output_types

        self.buffer = defaultdict(list)
        self.buffer_lock = threading.Lock()
        self.pending_futures: dict[Future, (int, int)] = dict()
        self.futures_lock = threading.Lock()

        self._shutdown_event = Event()
        self._last_flush_time = time.time()

        self.submit_export_pool = ThreadPoolExecutor(max_workers=export_workers)
        self._flush_thread = Thread(target=self._flush_loop)
        self._flush_thread.daemon = True
        self._flush_thread.start()

        self._setup_signal_handlers()

        self.success_callback = success_callback
        self.exception_callback = exception_callback

        self.logger = logging.getLogger(__name__)

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        self.logger.info("Received shutdown signal, flushing buffer...")
        self.flush_buffer()
        self._shutdown_event.set()

    def _handle_export_completion(self, future: Future):
        with self.futures_lock:
            start_block, end_block = self.pending_futures[future]
            self.pending_futures.pop(future)

        try:
            future.result()

            try:
                self.success_callback(end_block)
            except Exception as e:
                self.logger.error(f"Writing last synced block number {end_block} error.")

        except Exception as e:
            exception_details = get_exception_details(e)
            self.exception_callback(self.required_output_types, start_block, end_block, "export", exception_details)
            self.logger.error(f"Exporting items error: {exception_details}")
            if CRASH_INSTANTLY:
                self.shutdown()

    def write(self, records: Dict):
        with self.buffer_lock:
            for dataclass in records.keys():
                if dataclass in self.required_output_types or dataclass == "block":
                    self.buffer[dataclass].extend(records[dataclass])

        if len(self.buffer["block"]) >= self.max_buffer_size or not ASYNC_SUBMIT:
            return self.flush_buffer()
        return True

    def _should_flush(self) -> bool:
        current_time = time.time()
        time_since_last_flush = (current_time - self._last_flush_time) * 1000

        return len(self.buffer["block"]) >= self.block_size or time_since_last_flush >= self.linger_ms

    def export_items(self, items):
        for item_exporter in self.item_exporters:
            item_exporter.open()
            item_exporter.export_items(items)
            item_exporter.close()

    def flush_buffer(self):

        with self.buffer_lock:
            if len(self.buffer["block"]) == 0:
                return
            self.buffer["block"].sort(key=lambda x: x.number)
            block_range = (self.buffer["block"][0].number, self.buffer["block"][-1].number)
            flush_items = []
            for key in self.buffer:
                if key in self.required_output_types:
                    flush_items.extend(self.buffer[key])

            self.buffer.clear()
        self.logger.info(f"Flush data between block range: {block_range}")
        future = self.submit_export_pool.submit(self.export_items, flush_items)
        future.add_done_callback(self._handle_export_completion)

        with self.futures_lock:
            self.pending_futures[future] = block_range

        if not ASYNC_SUBMIT:
            try:
                future.result()
                return True
            except Exception as e:
                return False

        self._last_flush_time = time.time()
        return True

    def _flush_loop(self):
        while not self._shutdown_event.is_set():
            try:
                if self._should_flush():
                    self.flush_buffer()
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in flush loop: {e}")

    def shutdown(self):
        if self._shutdown_event.is_set():
            return

        self.logger.info("Shutting down buffer service...")
        self._handle_shutdown(None, None)
        self._flush_thread.join()
        self.submit_export_pool.shutdown(wait=True)
        self.logger.info("Buffer service shut down completed")
