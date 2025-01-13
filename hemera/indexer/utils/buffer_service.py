#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/11/19 下午6:07
Author  : xuzh
Project : hemera_indexer
"""
import json
import logging
import os
import signal
import threading
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from distutils.util import strtobool
from threading import Event
from typing import Any, Callable, Dict, List

from hemera.common.utils.exception_control import FastShutdownError, get_exception_details

BUFFER_BLOCK_SIZE = int(os.environ.get("BUFFER_BLOCK_SIZE", "1"))
MAX_BUFFER_SIZE = int(os.environ.get("MAX_BUFFER_SIZE", "1"))
ASYNC_SUBMIT = bool(strtobool(os.environ.get("ASYNC_SUBMIT", "false")))
CONCURRENT_SUBMITTERS = int(os.environ.get("CONCURRENT_SUBMITTERS", "1"))
CRASH_INSTANTLY = bool(strtobool(os.environ.get("CRASH_INSTANTLY", "true")))
EXPORT_STRATEGY = json.loads(os.environ.get("EXPORT_STRATEGY", "{}"))


class KeyLockContext:

    def __init__(self, manager, key, lock):
        self._manager = manager
        self._key = key
        self._lock = lock

    def __enter__(self):
        self._lock.acquire()

        with self._manager._meta_lock:
            self._manager._active_row_locks.add(self._key)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            with self._manager._meta_lock:
                self._manager._active_row_locks.discard(self._key)
                should_notify = len(self._manager._active_row_locks) == 0

            if should_notify:
                with self._manager._global_condition:
                    self._manager._global_condition.notify_all()
        finally:
            self._lock.release()


class BufferLockManager:
    def __init__(self):
        self._global_lock = threading.Lock()
        self._global_condition = threading.Condition(self._global_lock)

        self._locks: Dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

        self._active_row_locks = set()

    def __getitem__(self, key: str) -> KeyLockContext:
        if self._global_lock.locked():
            with self._global_lock:
                pass

        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return KeyLockContext(self, key, self._locks[key])

    def acquire_global_lock(self, timeout=-1):
        if not self._global_lock.acquire(blocking=True, timeout=timeout):
            return False

        try:
            while self._active_row_locks:
                self._global_condition.wait()
            return True
        except Exception as e:
            if self._global_lock.locked():
                self._global_lock.release()
            raise RuntimeError(f"Failed to acquire global lock: {str(e)}")

    def release_global(self):
        try:
            self._global_condition.notify_all()
        finally:
            self._global_lock.release()

    def remove(self, key: str) -> None:
        with self._meta_lock:
            self._locks.pop(key, None)
            self._active_row_locks.discard(key)
            should_notify = len(self._active_row_locks) == 0

        if should_notify:
            with self._global_condition:
                self._global_condition.notify_all()

    def clear(self) -> None:
        with self._meta_lock:
            self._locks.clear()
            self._active_row_locks.clear()

        with self._global_condition:
            self._global_condition.notify_all()

    def __enter__(self):
        if not self.acquire_global_lock():
            raise RuntimeError("Failed to acquire global lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_global()


class BufferService:

    def __init__(
        self,
        item_exporters,
        required_output_types,
        block_size: int = BUFFER_BLOCK_SIZE,
        max_buffer_size: int = MAX_BUFFER_SIZE,
        export_workers: int = CONCURRENT_SUBMITTERS,
        success_callback: Callable = None,
        exception_callback: Callable = None,
    ):
        self.block_size = block_size
        self.max_buffer_size = max_buffer_size
        self.concurrent_submitters = threading.Semaphore(export_workers)

        self.item_exporters = item_exporters
        self.required_output_types = required_output_types

        self.buffer = defaultdict(list)
        self.buffer_lock = BufferLockManager()

        self.output_in_progress: dict[(int, int), set] = dict()
        self.futures_output: dict[Future, set] = dict()
        self.pending_futures: dict[Future, (int, int)] = dict()
        self.futures_lock = threading.Lock()

        self._shutdown_event = Event()

        self.submit_export_pool = ThreadPoolExecutor(max_workers=export_workers)

        self._setup_signal_handlers()

        self.success_callback = success_callback
        self.exception_callback = exception_callback

        self.export_strategy = EXPORT_STRATEGY

        self.logger = logging.getLogger(__name__)

    def keys(self) -> List[Any]:
        return self.buffer.keys()

    def __getitem__(self, key: str) -> List[Any]:
        with self.buffer_lock[key]:
            return self.buffer[key]

    def get(self, key: str, default: Any = None) -> List[Any]:
        with self.buffer_lock[key]:
            return self.buffer.get(key, default)

    def __setitem__(self, key: str, value: Any):
        with self.buffer_lock[key]:
            if isinstance(value, list):
                self.buffer[key] = value
            else:
                self.buffer[key] = [value]

    def __contains__(self, key: str) -> bool:
        return key in self.buffer.keys()

    def pop(self, key: str, default: Any = None) -> Any:
        with self.buffer_lock[key]:
            return self.buffer.pop(key, default)

    def extend(self, key: str, values: List[Any]):
        with self.buffer_lock[key]:
            self.buffer[key].extend(values)

    def append(self, key: str, value: Any):
        with self.buffer_lock[key]:
            self.buffer[key].append(value)

    def _get_data_snapshot(self) -> Dict[str, List[Any]]:
        snapshot = {}
        all_keys = set(self.buffer.keys())

        with self.buffer_lock:
            for key in all_keys:
                if key in self.buffer:
                    snapshot[key] = self.buffer[key].copy()
        return snapshot

    def _clear_exported_data(self, keys: List[str]):
        for key in keys:
            with self.buffer_lock[key]:
                if key in self.buffer:
                    del self.buffer[key]

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        # self.logger.info("Received shutdown signal, flushing buffer...")
        # self.flush_buffer(self.required_output_types)
        self._shutdown_event.set()

    def _handle_export_completion(self, future: Future):
        with self.futures_lock:
            start_block, end_block = self.pending_futures[future]
            complete_type = self.futures_output[future]

            self.pending_futures.pop(future)
            self.futures_output.pop(future)

        try:
            future.result()

            self.output_in_progress[(start_block, end_block)] -= complete_type
            if self.success_callback and len(self.output_in_progress[(start_block, end_block)]) == 0:
                try:
                    self.output_in_progress.pop((start_block, end_block))
                    self.success_callback(end_block)
                except Exception as e:
                    self.logger.error(f"Writing last synced block number {end_block} error.")

        except Exception as e:
            exception_details = get_exception_details(e)
            if self.exception_callback:
                self.exception_callback(self.required_output_types, start_block, end_block, "export", exception_details)
            self.logger.error(f"Exporting items error: {exception_details}")
            if CRASH_INSTANTLY:
                self.shutdown()
                raise FastShutdownError(f"Exporting items error: {exception_details}")

        finally:
            self.concurrent_submitters.release()

    def export_items(self, items):
        for item_exporter in self.item_exporters:
            item_exporter.open()
            item_exporter.export_items(items)
            item_exporter.close()

    def flush_buffer(self, start_block, end_block, flush_keys: List[str]):
        flush_items = []
        flush_type = set()
        with self.buffer_lock:
            block_range = (start_block, end_block)

            for key in flush_keys:
                if key in self.required_output_types:
                    flush_type.add(key)
                    flush_items.extend(self.buffer[key])
            if len(flush_type):
                self.logger.info(f"Flush domains: {','.join(flush_type)} between block range: {block_range}")
            else:
                return True

        with self.futures_lock:
            future = self.submit_export_pool.submit(self.export_items, flush_items)
            self.futures_output[future] = flush_type
            self.pending_futures[future] = block_range
            if block_range not in self.output_in_progress:
                self.output_in_progress[block_range] = set(self.required_output_types)

        future.add_done_callback(self._handle_export_completion)

        if not ASYNC_SUBMIT:
            try:
                future.result()
                return True
            except Exception as e:
                return False

        return True

    def check_and_flush(self, start_block, end_block, job_name: str = None, output_types: List[str] = None):
        if job_name in self.export_strategy:
            output_types = self.export_strategy[job_name]

        self.concurrent_submitters.acquire()

        try:
            if not ASYNC_SUBMIT:
                return self.flush_buffer(start_block, end_block, output_types)
            else:
                self.flush_buffer(start_block, end_block, output_types)
            return True
        finally:
            self.concurrent_submitters.release()

    def clear(self):
        with self.buffer_lock:
            self.buffer.clear()

    def shutdown(self):
        if self._shutdown_event.is_set():
            return

        self.logger.info("Shutting down buffer service...")
        self._handle_shutdown(None, None)
        self.submit_export_pool.shutdown(wait=True)
        self.logger.info("Buffer service shut down completed")

    def is_shutdown(self):
        return self._shutdown_event.is_set()
