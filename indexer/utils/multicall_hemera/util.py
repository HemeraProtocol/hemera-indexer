#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/20 14:13
# @Author  will
# @File  util.py.py
# @Brief
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import orjson
from mpire import WorkerPool

from common.utils.format_utils import hex_str_to_bytes
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.signature import _get_signature

logger = logging.getLogger(__name__)
from contextlib import contextmanager


class GlobalPoolManager:
    def __init__(self, processes=None):
        self.processes = processes or os.cpu_count()
        self.pool = None

    def get_pool(self):
        if self.pool is None:
            self.pool = WorkerPool(n_jobs=self.processes)
        return self.pool

    def parallel_process(self, func, data, chunk_size=10000):
        return self.get_pool().map(func, data, chunk_size=chunk_size)

    def close(self):
        if self.pool:
            self.pool.terminate()
            self.pool.join()
            self.pool = None

    @contextmanager
    def pool_context(self):
        try:
            yield self
        finally:
            self.close()


global_pool_manager = GlobalPoolManager()


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


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"function {func.__name__} time: {execution_time:.6f} s")
        return result

    return wrapper


def make_request_concurrent(make_request, chunks, max_workers=None):
    def single_request(chunk, index):
        logger.debug(f"single request {len(chunk)}")
        return index, make_request(params=orjson.dumps(chunk))

    if max_workers is None:
        max_workers = os.cpu_count() + 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(single_request, chunk[0], i): i for i, chunk in enumerate(chunks)}
        results = [None] * len(chunks)
        for future in as_completed(future_to_chunk):
            index, result = future.result()
            results[index] = result

    return results


sig = _get_signature("tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])")


def process_response(calls, result):
    logger.debug(f"{__name__}, calls {len(calls)}")
    block_id, _, outputs = sig.decode_data(hex_str_to_bytes(result))
    res = {}
    for call, (success, output) in zip(calls, outputs):
        res.update(Call.decode_output(output, call.signature, call.returns, success))
    return res
