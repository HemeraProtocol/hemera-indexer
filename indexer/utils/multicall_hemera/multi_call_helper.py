#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/4 18:38
# @Author  will
# @File  multi_call_helper.py
# @Brief
import logging
from collections import defaultdict
from typing import List

import orjson

from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import hex_str_to_bytes
from indexer.utils.multicall_hemera import Call, Multicall
from indexer.utils.multicall_hemera.abi import TRY_BLOCK_AND_AGGREGATE_FUNC
from indexer.utils.multicall_hemera.constants import GAS_LIMIT, get_multicall_address, get_multicall_network
from indexer.utils.multicall_hemera.util import make_request_concurrent, rebatch_by_size
from indexer.utils.provider import get_provider_from_uri


class MultiCallHelper:
    def __init__(self, web3, kwargs=None, logger=None):
        self.web3 = web3
        self.provider = get_provider_from_uri(self.web3.provider.endpoint_uri, batch=True)
        self.make_request = self.provider.make_request
        if not logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
        self.chain_id = self.web3.eth.chain_id

        self.batch_size = kwargs["batch_size"]
        self._is_batch = kwargs["batch_size"] > 1
        self._is_multi_call = kwargs["multicall"]
        self._works = kwargs["max_workers"]
        if not self._is_multi_call:
            self.logger.info("multicall is disabled")
            self.net = None
            self.multi_call = None
            self.deploy_block_number = 2**56
        else:
            self.net = get_multicall_network(self.chain_id)
            self.multi_call = Multicall([], require_success=False, chain_id=self.chain_id)
            self.deploy_block_number = self.net.deploy_block_number

    def validate_calls(self, calls):
        cnt = 0
        for call in calls:
            cnt += 1
            call.call_id = cnt
            # make sure returns is not configured
            call.returns = None
            if call.block_number is None:
                raise FastShutdownError("MultiCallHelper.validate_calls failed: block_number is None")

    def fetch_result(self, chunks):
        res = list(make_request_concurrent(self.make_request, chunks, self._works))
        return res

    def decode_result(self, wrapped_calls, res, chunks):
        for response_chunk, (_, wrapped_calls) in zip(res, chunks):
            for calls, res in zip(wrapped_calls, response_chunk):
                result = res.get("result")
                if result:
                    self.logger.debug(f"{__name__}, calls {len(calls)}")
                    block_id, _, outputs = TRY_BLOCK_AND_AGGREGATE_FUNC.decode_data(hex_str_to_bytes(result))
                    for call, (success, output) in zip(calls, outputs):
                        call.returns = Call.decode_output(output, call.function_abi, call.returns, success)

    def execute_calls(self, calls: List[Call]) -> List[Call]:
        """execute eth calls
        1. check every call have a block number, this is must
        2. according to multicall contract launch block_number, split these calls into two lists. one can execute through multicall, while the other cannot
        3. for some reason, multicall may fail. re_collect these calls
        4. execute left calls directly through rpc
        5. return the calls, with result enriched
        """
        self.validate_calls(calls)
        to_execute_batch_calls, to_execute_multi_calls = self.prepare_calls(calls)
        multicall_rpc = self.construct_multicall_rpc(to_execute_multi_calls)
        chunks = list(rebatch_by_size(multicall_rpc, to_execute_multi_calls))
        self.logger.info(f"multicall helper after chunk, got={len(chunks)}")
        res = self.fetch_result(chunks)
        self.decode_result(to_execute_multi_calls, res, chunks)
        for cls in to_execute_multi_calls:
            for cl in cls:
                if cl.returns is None:
                    to_execute_batch_calls.append(cl)
        self.fetch_raw_calls(to_execute_batch_calls)
        return calls

    def fetch_raw_calls(self, calls: List[Call]):
        rpc_param = []
        for call in calls:
            rpc_param.append(call.to_rpc_param())
        if self._is_batch:
            response = self.make_request(params=orjson.dumps(rpc_param))
        else:
            response = [self.make_request(params=orjson.dumps(rpc_param[0]))]
        for call, data in zip(calls, response):
            result = data.get("result")
            call.returns = Call.decode_output(hex_str_to_bytes(result), call.signature, call.returns, None)

    def prepare_calls(self, calls: List[Call]):
        grouped_data = defaultdict(list)
        for call in calls:
            grouped_data[call.block_number].append(call)

        to_execute_batch_calls = []
        to_execute_multi_calls = []

        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number or not self._is_multi_call:
                to_execute_batch_calls.extend(items)
            else:
                to_execute_multi_calls.append(items)
        return to_execute_batch_calls, to_execute_multi_calls

    def construct_multicall_rpc(self, to_execute_multi_calls):
        multicall_rpc = []
        if to_execute_multi_calls:
            for calls in to_execute_multi_calls:
                multicall_rpc.append(
                    Multicall(
                        calls,
                        require_success=False,
                        chain_id=self.chain_id,
                        block_number=calls[0].block_number,
                        gas_limit=len(calls) * GAS_LIMIT,
                    ).to_rpc_param()
                )
        return multicall_rpc
