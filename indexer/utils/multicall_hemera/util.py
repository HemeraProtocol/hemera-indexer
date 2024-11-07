#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/20 14:13
# @Author  will
# @File  util.py.py
# @Brief
import logging
import os
import time
from concurrent.futures import as_completed

from concurrent.futures import ThreadPoolExecutor
import atexit
import threading
import orjson

logger = logging.getLogger(__name__)


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"function {func.__name__} time: {execution_time:.6f} s")
        print(f"function {func.__name__} time: {execution_time:.6f} s")
        return result

    return wrapper


def estimate_size(item):
    """return size in bytes"""
    return len(orjson.dumps(item))


def rebatch_by_size(items, same_length_calls, max_size=1024 * 250):
    # 250KB
    current_chunk = []
    calls = []
    current_size = 0
    for idx, item in enumerate(items):
        item_size = estimate_size(item)
        if current_size + item_size > max_size and current_chunk:
            logger.debug(f"current chunk size {len(current_chunk)}")
            yield (current_chunk, calls)
            current_chunk = []
            calls = []
            current_size = 0
        current_chunk.append(item)
        calls.append(same_length_calls[idx])
        current_size += item_size
    if current_chunk:
        logger.debug(f"current chunk size {len(current_chunk)}")
        yield (current_chunk, calls)


def make_request_concurrent(make_request, chunks, max_workers=None):
    def single_request(chunk, index):
        logger.debug(f"single request {len(chunk)}")
        return index, make_request(params=orjson.dumps(chunk))

    if max_workers is None:
        max_workers = os.cpu_count() + 4

    return ThreadPoolManager.submit_tasks(
            single_request,
            chunks,
            max_workers
        )


class ThreadPoolManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, max_workers=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ThreadPoolExecutor(max_workers=max_workers)
                    atexit.register(cls.shutdown)
        return cls._instance

    @classmethod
    def shutdown(cls):
        if cls._instance:
            cls._instance.shutdown(wait=False)
            cls._instance = None

    @classmethod
    def submit_tasks(cls, func, chunks, max_workers=None):
        executor = cls.get_instance(max_workers)
        results = [None] * len(chunks)

        try:
            future_to_chunk = {
                executor.submit(func, chunk[0], i): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(future_to_chunk):
                try:
                    index, result = future.result(timeout=30)  # 添加超时控制
                    results[index] = result
                except TimeoutError:
                    # 处理超时
                    pass
                except Exception as e:
                    # 处理其他异常
                    pass

        except Exception as e:
            # 处理提交任务时的异常
            pass

        return results
