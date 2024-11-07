#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/4 18:38
# @Author  will
# @File  multi_call_helper.py
# @Brief
import logging
from collections import defaultdict
from typing import List

import mpire

from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str
from indexer.utils.multicall_hemera import Call, Multicall
from indexer.utils.multicall_hemera.abi import TRY_BLOCK_AND_AGGREGATE_FUNC
from indexer.utils.multicall_hemera.constants import GAS_LIMIT, get_multicall_network
from indexer.utils.multicall_hemera.util import calculate_execution_time, make_request_concurrent, rebatch_by_size
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
        self.max_workers = kwargs["max_workers"]
        self._is_multi_call = kwargs["multicall"]
        if not self._is_multi_call:
            self.logger.info("multicall is disabled")
            self.net = None
            self.deploy_block_number = 2**56
        else:
            self.net = get_multicall_network(self.chain_id)
            self.deploy_block_number = self.net.deploy_block_number

    @calculate_execution_time
    def validate_and_prepare_calls(self, calls):
        grouped_data = defaultdict(list)
        cnt = 0
        for call in calls:
            cnt += 1
            call.call_id = cnt
            # make sure returns is not configured
            call.returns = None
            if call.block_number is None:
                raise FastShutdownError("MultiCallHelper.validate_calls failed: block_number is None")
            grouped_data[call.block_number].append(call)

        to_execute_batch_calls = []
        to_execute_multi_calls = []

        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number or not self._is_multi_call:
                to_execute_batch_calls.extend(items)
            else:
                to_execute_multi_calls.append(items)
        return to_execute_batch_calls, to_execute_multi_calls

    @calculate_execution_time
    def fetch_result(self, chunks):
        res = list(make_request_concurrent(self.make_request, chunks, self.max_workers))
        return res

    @calculate_execution_time
    def decode_result(self, wrapped_calls, res, chunks):
        for response_chunk, (_, wrapped_calls) in zip(res, chunks):
            for calls, res in zip(wrapped_calls, response_chunk):
                result = res.get("result")
                if result:
                    self.logger.debug(f"{__name__}, calls {len(calls)}")
                    dic = TRY_BLOCK_AND_AGGREGATE_FUNC.decode_function_output_data(result)
                    outputs = dic["returnData"]
                    for call, (output) in zip(calls, outputs):
                        call.returns = call.decode_output(bytes_to_hex_str(output["returnData"]))

    @calculate_execution_time
    def execute_calls(self, calls: List[Call]) -> List[Call]:
        """Execute eth calls
        1. Validate that each call has a specified block number (required)
        2. Split calls into two groups based on multicall contract deployment block:
           - Calls that can be executed via multicall contract
           - Calls that must be executed directly (before multicall deployment)
        3. Handle failed multicall executions by collecting failed calls
        4. Execute remaining calls directly through RPC
        5. Return all calls with their execution results attached
        """
        to_execute_batch_calls, to_execute_multi_calls = self.validate_and_prepare_calls(calls)
        if len(to_execute_multi_calls) > 0:
            multicall_rpc = self.construct_multicall_rpc(to_execute_multi_calls)
            chunks = list(rebatch_by_size(multicall_rpc, to_execute_multi_calls))
            self.logger.info(f"multicall helper after chunk, got={len(chunks)}")
            res = self.fetch_result(chunks)
            self.decode_result(to_execute_multi_calls, res, chunks)
            for cls in to_execute_multi_calls:
                for cl in cls:
                    if cl.returns is None:
                        to_execute_batch_calls.append(cl)
        if len(to_execute_batch_calls) > 0:
            self.logger.info(f"multicall helper batch call, got={len(to_execute_batch_calls)}")
            self.fetch_raw_calls(to_execute_batch_calls)
        return calls

    @calculate_execution_time
    def fetch_raw_calls(self, calls: List[Call]):
        batch_call_list = []
        batch_rpc_param_list = []

        for call in calls:
            batch_call_list.append(call)
            batch_rpc_param_list.append(call.rpc_param)
        wrapped_rpc_param_list = [
            (batch_rpc_param_list[i : i + self.batch_size], i)
            for i in range(0, len(batch_rpc_param_list), self.batch_size)
        ]
        wrapped_call_list = [
            (batch_call_list[i : i + self.batch_size]) for i in range(0, len(batch_call_list), self.batch_size)
        ]

        result = list(make_request_concurrent(self.make_request, wrapped_rpc_param_list, self.max_workers))

        for calls, batch_result in zip(wrapped_call_list, result):
            for call, data in zip(calls, batch_result):
                result = data.get("result")
                try:
                    call.returns = call.decode_output(result)
                except Exception:
                    call.returns = None
                    self.logger.warning(f"multicall helper failed call: {call}")

    # @calculate_execution_time
    # def construct_multicall_rpc(self, to_execute_multi_calls):
    #     logging.info(f"function total multicalls {len(to_execute_multi_calls)}")
    #     multicall_rpc = []
    #     if to_execute_multi_calls:
    #         for calls in to_execute_multi_calls:
    #             multicall_rpc.append(
    #                 Multicall(
    #                     calls,
    #                     require_success=False,
    #                     chain_id=self.chain_id,
    #                     block_number=calls[0].block_number,
    #                     gas_limit=(len(calls) * GAS_LIMIT),
    #                 ).to_rpc_param()
    #             )
    #     return multicall_rpc

    def construct_multicall_rpc(self, to_execute_multi_calls):
        logging.info(f"Function total multicalls: {len(to_execute_multi_calls)}")
        to_execute_multi_calls = [(calls, ) for calls in  to_execute_multi_calls]
        with mpire.WorkerPool() as pool:
            multicall_rpcs = pool.map(
                self._construct_single_multicall_rpc,
                to_execute_multi_calls
            )

        return multicall_rpcs

    def _construct_single_multicall_rpc(self, calls):

        multicall = Multicall(
            calls,
            require_success=False,
            chain_id=self.chain_id,
            block_number=calls[0].block_number,
            gas_limit=(len(calls) * GAS_LIMIT),
        )
        return multicall.to_rpc_param()
