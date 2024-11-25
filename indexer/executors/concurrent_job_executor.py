#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/11/14 下午3:21
Author  : xuzh
Project : hemera_indexer
"""
import logging
from collections import deque
from queue import Empty, Queue
from threading import Event, Semaphore, Thread

from mpire import WorkerPool

from common.utils.exception_control import get_exception_details


class ConcurrentJobExecutor:

    def __init__(self, buffer_service, max_processors=1, call_back=None, error_callback=None):
        self.buffer_service = buffer_service
        self.pool = WorkerPool(n_jobs=max_processors, use_dill=True, start_method="spawn")
        self.call_back = call_back
        self.error_callback = error_callback

        self.running_tasks = {}
        self.results = {}
        self.task_count = 0

        self.processors = {f"processor-{i}": True for i in range(max_processors)}
        self.available_processors = deque(f"processor-{i}" for i in range(max_processors))
        self.processor_semaphore = Semaphore(max_processors)
        self.shutdown_event = Event()

        self.task_queue = Queue()

        self.task_processor = Thread(target=self._process_tasks)
        self.task_processor.daemon = True
        self.task_processor.start()

        self.logger = logging.getLogger(__name__)

    def _allocate_processor(self):
        if len(self.available_processors) > 0:
            processor = self.available_processors.popleft()
            self.processors[processor] = False
            return processor
        return None

    def _release_processor(self, processor):
        self.processors[processor] = True
        self.processor_semaphore.release()
        self.available_processors.append(processor)

    def _process_tasks(self):
        while not self.shutdown_event.is_set():
            try:
                try:
                    task = self.task_queue.get(timeout=1)
                except Empty:
                    continue

                try:
                    processor = self._allocate_processor()
                    task["kwargs"]["processor"] = processor
                    self.pool.apply_async(
                        task["func"],
                        task["args"],
                        task["kwargs"],
                        callback=lambda result, p=processor, param=task["kwargs"]: self._handle_task_completion(
                            result, p, param
                        ),
                        error_callback=lambda error, p=processor, param=task["kwargs"]: self._handle_task_failed(
                            error, p, param
                        ),
                    )
                except Exception as e:
                    self.logger.error(f"Error processing task: {str(e)}")
                    self.processor_semaphore.release()

            except Exception as e:
                self.logger.error(f"Unexpected error in task processor: {e}")

    def _handle_task_completion(self, result, processor, param):
        self._release_processor(processor)
        self.logger.info(f"Task with parameter:{param} completed successfully by processor: {processor}")

        self.buffer_service.write(result)

        if self.call_back:
            param["processor"] = processor
            self.call_back(**param)

    def _handle_task_failed(self, error, processor, param):
        self.logger.error(f"with parameter:{param} failed in processor:{processor} error: {error}")
        self._release_processor(processor)

        if self.error_callback:
            try:
                param["processor"] = processor
                error_details = get_exception_details(error)
                self.error_callback(
                    output_types=self.buffer_service.required_output_types,
                    start_block=param["start_block"],
                    end_block=param["end_block"],
                    exception_stage="Job Running",
                    exception=error_details,
                )
            except Exception as e:
                self.logger.error(f"An exception occurred while execute call back function. error: {e}")

    def submit(self, func, *args, **kwargs):
        self.processor_semaphore.acquire()

        try:
            task = {"func": func, "args": args, "kwargs": kwargs}
            self.task_queue.put(task)

        except Exception as e:
            self.processor_semaphore.release()
            raise e

    def shutdown(self):
        self.shutdown_event.set()
        self.task_processor.join()
        self.pool.join(keep_alive=True)
        self.pool.terminate()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
