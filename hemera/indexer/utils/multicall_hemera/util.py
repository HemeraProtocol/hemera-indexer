#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/20 14:13
# @Author  will
# @File  util.py.py
# @Brief
import atexit
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import orjson
from requests import RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from hemera.indexer.utils.multicall_hemera.constants import RPC_PAYLOAD_SIZE

logger = logging.getLogger(__name__)


JOB_RETRIES = int(os.environ.get("JOB_RETRIES", "5"))


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


def rebatch_by_size(items, same_length_calls, max_size=1024 * RPC_PAYLOAD_SIZE):
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

    return ThreadPoolManager.submit_tasks(single_request, chunks, max_workers)


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
    @retry(
        stop=stop_after_attempt(JOB_RETRIES),
        wait=wait_exponential(min=1, max=(2 ** (JOB_RETRIES - 1)), multiplier=2),
        retry=retry_if_exception_type((TimeoutError, ConnectionError, RequestException, Exception)),
        reraise=True,
    )
    def submit_tasks(cls, func, chunks, max_workers=None):
        executor = cls.get_instance(max_workers)
        results = [None] * len(chunks)

        try:
            future_to_chunk = {executor.submit(func, chunk[0], i): i for i, chunk in enumerate(chunks)}

            for future in as_completed(future_to_chunk):
                index, result = future.result(timeout=30)
                results[index] = result
        except Exception as e:
            logger.error(f"ThreadPoolManager.submit_tasks error: {e}")
            raise e

        return results
