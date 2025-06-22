#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/20 14:13
# @Author  will
# @File  util.py
# @Brief
import atexit
import json
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
        # print(f"function {func.__name__} time: {execution_time:.6f} s")
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
    def check_results(cls, results):
        try:
            if results:
                for result in results:
                    if isinstance(result, dict) and "error" in result:
                        error = result["error"]
                        if error.get("code") == 429:
                            # raise it to retry
                            raise Exception(f"Rate limit error: {error.get('message')}")
                        else:
                            # {'error': {'code': -32000, 'message': 'out of gas'}}
                            # {'error': {'code': -32000, 'message': 'execution reverted'}
                            if "out of gas" in error.get("message"):
                                # if out of gas, log the error
                                logger.error(f"rpc error: {json.dumps(result)}")
            return results
        except Exception as e:
            raise e

    @classmethod
    def submit_tasks(cls, func, chunks, max_workers=None):
        executor = cls.get_instance(max_workers)
        results = [None] * len(chunks)

        pending_tasks = {i: chunk for i, chunk in enumerate(chunks)}
        last_time_tasks = len(pending_tasks)
        attempt = 0
        max_attempts = JOB_RETRIES
        min_wait = 1
        max_wait = 2 ** (JOB_RETRIES - 1)

        while pending_tasks and attempt < max_attempts:
            futures = {executor.submit(func, chunk[0], i): i for i, chunk in pending_tasks.items()}
            pending_tasks.clear()

            for future in as_completed(futures):
                try:
                    index, result = future.result(timeout=30)
                    cls.check_results(result)
                    results[index] = result
                except Exception as e:
                    # logger.error(f"Task {index} failed with error: {e}")
                    pending_tasks[index] = chunks[index]

            if pending_tasks:
                if len(pending_tasks) < last_time_tasks:
                    # some task succeed, reset attempt
                    delay = 0
                    attempt = 0
                else:
                    delay = min(min_wait * (2**attempt), max_wait)
                    attempt += 1
                last_time_tasks = len(pending_tasks)
                logger.info(f"Retrying {len(pending_tasks)} failed tasks in {delay} seconds...")
                time.sleep(delay)

        if pending_tasks:
            logger.error(f"Some tasks failed after {max_attempts} retries: {list(pending_tasks.keys())}")
            raise Exception(f"Some tasks failed after {max_attempts} retries: {list(pending_tasks.keys())}")

        return results
