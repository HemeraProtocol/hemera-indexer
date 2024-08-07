#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/7 13:44
# @Author  will
# @File  multi_call_util.py
# @Brief use the `multicall` contract to fetch data
import json
import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from functools import lru_cache
from operator import itemgetter

from eth_abi import abi

from common.utils.format_utils import to_snake_case
from enumeration.record_level import RecordLevel
from enumeration.token_type import TokenType
from indexer.domain.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from indexer.utils.abi import encode_abi, function_abi_to_4byte_selector_str
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.multicall_hemera import Call, Multicall, Network
from indexer.utils.multicall_hemera.util import (
    calculate_execution_time,
    make_request_concurrent,
    process_response,
    rebatch_by_size,
)
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

BALANCE_OF_ERC20 = "balanceOf(address)(uint256)"
BALANCE_OF_ERC1155 = "balanceOf(address,uint256)(uint256)"

exception_recorder = ExceptionRecorder()


class MultiCallProxy:

    def __init__(self, web3, kwargs=None, logger=None):
        self.web3 = web3
        self.provider = get_provider_from_uri(self.web3.provider.endpoint_uri, batch=True)
        self.make_request = self.provider.make_request
        if not logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
        self.chain_id = self.web3.eth.chain_id
        self.multi_call = Multicall([], require_success=False, chain_id=self.chain_id)
        self.net = Network.from_value(self.chain_id)
        self.deploy_block_number = self.net.deploy_block_number
        self.chunk_size = 1000
        self.batch_size = kwargs["batch_size"]
        self._is_batch = kwargs["batch_size"] > 1
        self._is_multi_call = kwargs["multicall"]
        if not self._is_multi_call:
            self.logger.info("multicall is disabled")

        self.token_k_fields = ("address", "token_address", "block_number", "token_type", "token_id")
        self.contract_k_fields = ("address",)
        self.token_ids_infos_k_fields = ("address", "token_id", "token_type", "is_get_token_uri")
        self.wrong_call_k_fileds = ("block_number", "target", "function")

    @calculate_execution_time
    def _prepare_token_ids_info_parameters(self, token_info_items):
        to_execute_batch_calls = []
        wrapped_calls = []
        sorted_items = sorted(token_info_items, key=itemgetter("block_number"))
        grouped_data = defaultdict(list)
        for row in sorted_items:
            grouped_data[row["block_number"]].append(row)
        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number or not self._is_multi_call:
                to_execute_batch_calls.extend(items)
            else:
                calls = []
                for row in items:
                    construct_call = None
                    address = row["address"]
                    if row["token_type"] == TokenType.ERC721.value:
                        if row["is_get_token_uri"] is True:
                            construct_call = Call(
                                address,
                                ["tokenURI(uint256)(string)", row["token_id"]],
                                [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                block_id=block_id,
                            )

                        else:
                            construct_call = Call(
                                address,
                                ["ownerOf(uint256)(address)", row["token_id"]],
                                [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                block_id=block_id,
                            )
                    elif row["token_type"] == TokenType.ERC1155.value:
                        if row["is_get_token_uri"] is True:
                            construct_call = Call(
                                address,
                                ["uri(uint256)(string)", row["token_id"]],
                                [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                block_id=block_id,
                            )

                        else:
                            construct_call = Call(
                                address,
                                ["totalSupply(uint256)(uint256)", row["token_id"]],
                                [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                block_id=block_id,
                            )

                    if construct_call:
                        calls.append(construct_call)
                wrapped_calls.append(calls)
        return wrapped_calls, to_execute_batch_calls

    def create_token_detail(self, token_info, value, decode_flag):
        common_args = {
            "token_address": token_info["address"],
            "token_id": token_info["token_id"],
            "block_number": token_info["block_number"],
            "block_timestamp": token_info["block_timestamp"],
        }
        try:

            if token_info["is_get_token_uri"]:
                token_uri = decode_string(value) if decode_flag else value
                if token_info["token_type"] == "ERC721":
                    return [ERC721TokenIdDetail(**common_args, token_uri=token_uri)]
                else:
                    return [ERC1155TokenIdDetail(**common_args, token_uri=token_uri)]
            else:
                if token_info["token_type"] == "ERC721":
                    token_owner = decode_address(value) if decode_flag else value
                    return [
                        UpdateERC721TokenIdDetail(**common_args, token_owner=token_owner),
                        ERC721TokenIdChange(**common_args, token_owner=token_owner),
                    ]
                else:
                    token_supply = decode_uint256(value) if decode_flag else value
                    return [UpdateERC1155TokenIdDetail(**common_args, token_supply=token_supply)]
        except Exception as e:
            exception_recorder.log(
                block_number=token_info.block_number,
                dataclass=to_snake_case("token_id_info"),
                message_type="decode_token_id_info_fail",
                message=str(e),
                exception_env=asdict(token_info),
                level=RecordLevel.WARN,
            )

    @calculate_execution_time
    def fetch_token_ids_info(self, token_info_items):
        # export token_ids_info
        self.logger.info(f"MultiCallProxy fetch_token_ids_info size={len(token_info_items)}")
        wrapped_calls, to_execute_batch_calls = self._prepare_token_ids_info_parameters(token_info_items)

        return_data_map = {self.build_key(it, self.token_ids_infos_k_fields): it for it in token_info_items}

        multicall_result = {}
        multicall_rpc = []
        return_data = []

        if wrapped_calls:
            for calls in wrapped_calls:
                self.multi_call.calls = calls
                self.multi_call.block_id = calls[0].block_id
                rpc_para = self.multi_call.to_rpc_param()
                multicall_rpc.append(rpc_para)

            for idx, body in enumerate(multicall_rpc):
                body["request_id"] = idx

            chunks = list(rebatch_by_size(multicall_rpc, wrapped_calls))
            self.logger.info(f"after chunk got {len(chunks)}")

            res = self.fetch_result(chunks)
            tmp = self.decode_result(wrapped_calls, res, chunks)
            multicall_result.update(tmp)

        for k, v in multicall_result.items():
            if v is not None:
                tmp = self.create_token_detail(return_data_map[k], v, decode_flag=False)
                return_data.extend(tmp)
            else:
                to_execute_batch_calls.append(return_data_map[k])

        raw_result = self.fetch_to_execute_batch_calls(self._token_ids_info_rpc_requests, to_execute_batch_calls)

        for token_info in token_info_items:
            bk = self.build_key(token_info, self.token_ids_infos_k_fields)
            decode_flag = True
            if bk in multicall_result and multicall_result[bk] is not None:
                value = multicall_result[bk]
                decode_flag = False
            elif bk in raw_result:
                value = raw_result[bk]
            else:
                value = None
            if not value:
                decode_flag = False
            tmp = self.create_token_detail(token_info, value, decode_flag)
            return_data.extend(tmp)
        return return_data

    def _token_ids_info_rpc_requests(self, token_info_items):

        eth_calls = list(
            generate_eth_call_json_rpc(
                [
                    {
                        "request_id": item["request_id"],
                        "param_to": item["address"],
                        "param_data": abi_selector_encode_and_decode_type(item),
                        "param_number": hex(item["block_number"]),
                    }
                    for item in token_info_items
                ]
            )
        )

        return_dic = {}
        if self._is_batch:
            response = self.make_request(params=json.dumps(eth_calls))
        else:
            response = [self.make_request(params=json.dumps(eth_calls[0]))]

        for token_info, data in zip(token_info_items, response):
            k = self.build_key(token_info, self.token_ids_infos_k_fields)
            result = rpc_response_to_result(data)
            value = result[2:] if result is not None else None
            return_dic[k] = value
        return return_dic

    @calculate_execution_time
    def _prepare_token_balance_parameters(self, tokens):
        sorted_items = sorted(tokens, key=itemgetter("block_number"))
        grouped_data = defaultdict(list)
        for row in sorted_items:
            grouped_data[row["block_number"]].append(row)

        to_execute_batch_calls = []
        wrapped_calls = []

        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number or not self._is_multi_call:
                to_execute_batch_calls.extend(items)
            else:
                calls = []
                for row in items:
                    token, wal = row["token_address"], row["address"]
                    token_id = row["token_id"]
                    token_type = row["token_type"]
                    if token_type == "ERC1155" and token_id is not None:
                        construct_call = Call(
                            token,
                            [BALANCE_OF_ERC1155, wal, token_id],
                            [(self.build_key(row, self.token_k_fields), None)],
                            block_id=block_id,
                        )
                    else:
                        construct_call = Call(
                            token,
                            [BALANCE_OF_ERC20, wal],
                            [(self.build_key(row, self.token_k_fields), None)],
                            block_id=block_id,
                        )
                    if construct_call:
                        calls.append(construct_call)
                wrapped_calls.append(calls)

        return wrapped_calls, to_execute_batch_calls

    @calculate_execution_time
    def fetch_result(self, chunks):
        res = list(make_request_concurrent(self.make_request, chunks, os.cpu_count() * 2))
        return res

    @calculate_execution_time
    def decode_result(self, wrapped_calls, res, chunks):
        rr = {}
        for response_chunk, (_, wrapped_calls) in zip(res, chunks):
            for calls, res in zip(wrapped_calls, response_chunk):
                result = res.get("result")
                if result:
                    rr.update(process_response(calls, result))
        return rr

    @calculate_execution_time
    def fetch_to_execute_batch_calls(self, func, to_execute_batch_calls):
        if not to_execute_batch_calls:
            return {}
        rr = {}
        chunks = list(self.chunk_list(to_execute_batch_calls, self.batch_size))
        with ThreadPoolExecutor(os.cpu_count() * 2) as executor:
            results = list(executor.map(func, chunks))
        for tmp in results:
            rr.update(tmp)
        return rr

    @calculate_execution_time
    def fetch_token_balance(self, tokens):
        self.logger.info(f"MultiCallProxy fetch_token_balance size={len(tokens)}")
        wrapped_calls, to_execute_batch_calls = self._prepare_token_balance_parameters(tokens)

        return_data_map = {self.build_key(it, self.token_k_fields): it for it in tokens}

        multicall_result = {}
        multicall_rpc = []
        if wrapped_calls:
            for calls in wrapped_calls:
                self.multi_call.calls = calls
                self.multi_call.block_id = calls[0].block_id
                rpc_para = self.multi_call.to_rpc_param()
                multicall_rpc.append(rpc_para)

            for idx, body in enumerate(multicall_rpc):
                body["request_id"] = idx

            chunks = list(rebatch_by_size(multicall_rpc, wrapped_calls))
            self.logger.info(f"after chunk, got={len(chunks)}")
            res = self.fetch_result(chunks)
            tmp = self.decode_result(wrapped_calls, res, chunks)
            multicall_result.update(tmp)
        for k, v in multicall_result.items():
            if v is not None:
                return_data_map[k]["balance"] = v
            else:
                to_execute_batch_calls.append(return_data_map[k])

        tmp = self.fetch_to_execute_batch_calls(self._token_balances, to_execute_batch_calls)
        multicall_result.update(tmp)

        return_data = []
        for item in tokens:
            bk = self.build_key(item, self.token_k_fields)
            balance = None
            if bk in multicall_result:
                balance = multicall_result[bk]
            return_data.append(
                {
                    "address": item["address"].lower(),
                    "token_id": item["token_id"],
                    "token_type": item["token_type"],
                    "token_address": item["token_address"].lower(),
                    "balance": balance,
                    "block_number": item["block_number"],
                    "block_timestamp": item["block_timestamp"],
                }
            )
        return return_data

    @calculate_execution_time
    def _token_balances(self, tokens):
        result_dic = {}
        for idx, token in enumerate(tokens):
            token["request_id"] = idx
        token_balance_rpc = list(generate_eth_call_json_rpc(tokens))

        if self._is_batch:
            response = self.make_request(params=json.dumps(token_balance_rpc))
        else:
            response = [self.make_request(params=json.dumps(token_balance_rpc[0]))]

        for data in list(zip_rpc_response(tokens, response)):
            result = rpc_response_to_result(data[1])
            balance = None

            try:
                if result:
                    balance = abi.decode(["uint256"], bytes.fromhex(result[2:]))[0]
                    result_dic[self.build_key(data[0], self.token_k_fields)] = balance

            except Exception as e:
                self.logger.warning(
                    f"Decoding token balance value failed. "
                    f"token address: {data[0]['token_address']}. "
                    f"rpc response: {result}. "
                    f"block number: {data[0]['block_number']}. "
                    f"exception: {e}. "
                )
                result_dic[self.build_key(data[0], self.token_k_fields)] = balance

        return result_dic

    @staticmethod
    @lru_cache(maxsize=20_0000)
    def build_key_in(record, fields):
        values = []
        for field in fields:
            try:
                values.append(str(next(value for name, value in record if name == field)))
            except StopIteration:
                pass
        return "|".join(values)

    @staticmethod
    def build_key(record, fields: tuple):
        if isinstance(record, dict):
            return MultiCallProxy.build_key_in(dict_to_tuple(record), fields)
        return MultiCallProxy.build_key_in(record, fields)

    @staticmethod
    def chunk_list(lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i : i + chunk_size]


def abi_selector_encode_and_decode_type(token_id_info):
    if token_id_info["token_type"] == TokenType.ERC721.value:
        if token_id_info["is_get_token_uri"]:
            return encode_abi(
                ERC721_TOKEN_URI_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc721_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC721_OWNER_OF_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc721_owner_of_sig_prefix,
            )
    elif token_id_info["token_type"] == TokenType.ERC1155.value:
        if token_id_info["is_get_token_uri"]:
            return encode_abi(
                ERC1155_TOKEN_URI_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc1155_token_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC1155_TOTAL_SUPPLY_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc1155_token_supply_sig_prefix,
            )


ERC721_TOKEN_URI_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "tokenURI",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC721_OWNER_OF_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "ownerOf",
    "outputs": [{"name": "", "type": "address"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC1155_TOKEN_URI_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "uri",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC1155_TOTAL_SUPPLY_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "totalSupply",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

erc721_uri_sig_prefix = function_abi_to_4byte_selector_str(ERC721_TOKEN_URI_ABI_FUNCTION)
erc721_owner_of_sig_prefix = function_abi_to_4byte_selector_str(ERC721_OWNER_OF_ABI_FUNCTION)

erc1155_token_uri_sig_prefix = function_abi_to_4byte_selector_str(ERC1155_TOKEN_URI_ABI_FUNCTION)
erc1155_token_supply_sig_prefix = function_abi_to_4byte_selector_str(ERC1155_TOTAL_SUPPLY_ABI_FUNCTION)


def dict_to_tuple(d):
    return tuple(sorted(d.items()))


def decode_string(value):
    return abi.decode(["string"], bytes.fromhex(value))[0].replace("\u0000", "")


def decode_address(value):
    return abi.decode(["address"], bytes.fromhex(value))[0]


def decode_uint256(value):
    return abi.decode(["uint256"], bytes.fromhex(value))[0]
