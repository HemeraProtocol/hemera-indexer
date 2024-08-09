#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/7 13:44
# @Author  will
# @File  multi_call_util.py
# @Brief aggregate many calls into one or several
import json
import logging
from itertools import groupby
from operator import itemgetter

from eth_abi import abi
from multicall import Call

from enumeration.record_level import RecordLevel
from enumeration.token_type import TokenType
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from indexer.utils.abi import encode_abi, function_abi_to_4byte_selector_str
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.extend_multicall import ExtendMulticall
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.network_util import Network
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

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
        self.multi_call = ExtendMulticall([], _w3=self.web3)
        self.net = Network.from_value(self.multi_call.chainid)
        self.deploy_block_number = self.net.deploy_block_number
        self.chunk_size = 1000
        self.batch_size = kwargs["batch_size"]
        self._is_batch = kwargs["batch_size"] > 1

        self.token_k_fields = ["address", "token_address", "block_number", "token_type", "token_id"]
        self.contract_k_fields = ["address"]
        self.token_ids_infos_k_fields = ["address", "token_id", "token_type", "is_get_token_uri"]

    def fetch_token_ids_info(self, token_info_items):
        # export token_ids_info
        self.logger.info(f"MultiCallUtil  fetch_token_ids_info size={len(token_info_items)}")
        sorted_items = sorted(token_info_items, key=itemgetter("block_number"))

        grouped_data = {k: list(v) for k, v in groupby(sorted_items, key=itemgetter("block_number"))}

        result = {}
        to_execute_batch_calls = []

        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number:
                to_execute_batch_calls.extend(items)
            else:
                for chunk in self.chunk_list(items, self.chunk_size):
                    try:
                        calls = []
                        for row in chunk:

                            address = row["address"]
                            if row["token_type"] == TokenType.ERC721.value:
                                if row["is_get_token_uri"] is True:
                                    calls.append(
                                        Call(
                                            address,
                                            ["tokenURI(uint256)(string)", row["token_id"]],
                                            [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                        )
                                    )
                                else:
                                    calls.append(
                                        Call(
                                            address,
                                            ["ownerOf(uint256)(address)", row["token_id"]],
                                            [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                        )
                                    )
                            elif row["token_type"] == TokenType.ERC1155.value:
                                if row["is_get_token_uri"] is True:
                                    calls.append(
                                        Call(
                                            address,
                                            ["uri(uint256)(string)", row["token_id"]],
                                            [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                        )
                                    )
                                else:
                                    calls.append(
                                        Call(
                                            address,
                                            ["totalSupply(uint256)(uint256)", row["token_id"]],
                                            [(self.build_key(row, self.token_ids_infos_k_fields), None)],
                                        )
                                    )

                        self.multi_call.calls = calls
                        self.multi_call.block_id = block_id
                        tmp = self.multi_call()
                        if tmp:
                            result.update(tmp)
                    except Exception as e:
                        # eth call
                        self.logger.warning(f"Exception while processing block {block_id}: {e}, downgrade to eth_call")
                        # for call in calls:
                        #     try:
                        #         call.w3 = self.web3
                        #         tt = call()
                        #     except Exception as call_e:
                        #         # locate the problem calls, where call_e raised, record it
                        #         self.logger.error(f"single call failed: e {call_e}, call {call}, args {call.args}, target {call.target}")
                        to_execute_batch_calls.extend(chunk)
        # batch call
        # need decode
        raw_result = {}
        if to_execute_batch_calls:
            for chunk in self.chunk_list(to_execute_batch_calls, self.batch_size):
                tmp = self._token_ids_info_rpc_requests(chunk)
                raw_result.update(tmp)
        return_data = []
        for token_info in token_info_items:
            bk = self.build_key(token_info, self.token_ids_infos_k_fields)
            decode_flag = True
            if bk in result:
                value = result[bk]
                decode_flag = False
            elif bk in raw_result:
                value = raw_result[bk]
            else:
                value = None
            if not value:
                decode_flag = False
            if token_info["token_type"] == "ERC721":
                if token_info["is_get_token_uri"]:
                    return_data.append(
                        ERC721TokenIdDetail(
                            token_address=token_info["address"],
                            token_id=token_info["token_id"],
                            token_uri=(
                                abi.decode(["string"], bytes.fromhex(value))[0].replace("\u0000", "")
                                if decode_flag
                                else value
                            ),
                            block_number=token_info["block_number"],
                            block_timestamp=token_info["block_timestamp"],
                        )
                    )
                else:
                    return_data.append(
                        UpdateERC721TokenIdDetail(
                            token_address=token_info["address"],
                            token_id=token_info["token_id"],
                            token_owner=abi.decode(["address"], bytes.fromhex(value))[0] if decode_flag else value,
                            block_number=token_info["block_number"],
                            block_timestamp=token_info["block_timestamp"],
                        )
                    )
                    return_data.append(
                        ERC721TokenIdChange(
                            token_address=token_info["address"],
                            token_id=token_info["token_id"],
                            token_owner=abi.decode(["address"], bytes.fromhex(value))[0] if decode_flag else value,
                            block_number=token_info["block_number"],
                            block_timestamp=token_info["block_timestamp"],
                        )
                    )
            else:
                if token_info["is_get_token_uri"]:
                    return_data.append(
                        ERC1155TokenIdDetail(
                            token_address=token_info["address"],
                            token_id=token_info["token_id"],
                            token_uri=(
                                abi.decode(["string"], bytes.fromhex(value))[0].replace("\u0000", "")
                                if decode_flag
                                else value
                            ),
                            block_number=token_info["block_number"],
                            block_timestamp=token_info["block_timestamp"],
                        )
                    )
                else:
                    return_data.append(
                        UpdateERC1155TokenIdDetail(
                            token_address=token_info["address"],
                            token_id=token_info["token_id"],
                            token_supply=abi.decode(["uint256"], bytes.fromhex(value))[0] if decode_flag else value,
                            block_number=token_info["block_number"],
                            block_timestamp=token_info["block_timestamp"],
                        )
                    )
        return return_data

    def _token_ids_info_rpc_requests(self, token_info_items):
        return_dic = {}
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

        if self._is_batch:
            response = self.make_request(params=json.dumps(eth_calls))
        else:
            response = [self.make_request(params=json.dumps(eth_calls[0]))]

        for token_info, data in zip(token_info_items, response):
            result = rpc_response_to_result(data)
            value = result[2:] if result is not None else None
            return_dic[self.build_key(token_info, self.token_ids_infos_k_fields)] = value
        return return_dic

    def fetch_token_balance(self, tokens):
        self.logger.info(f"MultiCallUtil  fetch_token_balance size={len(tokens)}")
        sorted_items = sorted(tokens, key=itemgetter("block_number"))

        grouped_data = {k: list(v) for k, v in groupby(sorted_items, key=itemgetter("block_number"))}

        result = {}
        to_execute_batch_calls = []
        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number:
                to_execute_batch_calls.extend(items)
            else:
                for chunk in self.chunk_list(items, self.chunk_size):
                    try:
                        calls = []
                        for row in chunk:
                            token, wal = row["token_address"], row["address"]
                            token_id = row["token_id"]
                            token_type = row["token_type"]
                            if token_type == "ERC1155" and token_id is not None:
                                calls.append(
                                    Call(
                                        token,
                                        ["balanceOf(address,uint256)(uint256)", wal, token_id],
                                        [(self.build_key(row, self.token_k_fields), None)],
                                    )
                                )
                            else:
                                calls.append(
                                    Call(
                                        token,
                                        ["balanceOf(address)(uint256)", wal],
                                        [(self.build_key(row, self.token_k_fields), None)],
                                    )
                                )
                        self.multi_call.calls = calls
                        self.multi_call.block_id = block_id
                        tmp = self.multi_call()
                        result.update(tmp)
                    except Exception as e:
                        self.logger.warning(
                            f"multi_call.fetch_token_balance failed. e {e} block_id={block_id} downgrade to eth_call"
                        )
                        #
                        # for call in calls:
                        # try:
                        #     call.w3 = self.web3
                        #     tt = call()
                        # except Exception as call_e:
                        #     # locate the problem calls, where call_e raised, record it
                        #     self.logger.error(f"balance single call failed: e {call_e}, call {call}, args {call.args}, target {call.target}")
                        to_execute_batch_calls.extend(chunk)
        if to_execute_batch_calls:
            for chunk in self.chunk_list(to_execute_batch_calls, self.batch_size):
                tmp = self._token_balances(chunk)
                result.update(tmp)
        return_data = []
        for item in tokens:
            bk = self.build_key(item, self.token_k_fields)
            balance = None
            if bk in result:
                balance = result[bk]
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
                exception_recorder.log(
                    block_number=data[0]["block_number"],
                    dataclass=TokenBalance.type(),
                    message_type="DecodeTokenBalanceFail",
                    message=str(e),
                    level=RecordLevel.WARN,
                )
                result_dic[self.build_key(data[0], self.token_k_fields)] = balance

        return result_dic

    @staticmethod
    def build_key(dic: dict, fields: list):
        return "|".join(map(str, (dic[field] for field in fields)))

    @staticmethod
    def chunk_list(lst, chunk_size):
        """将列表分割成指定大小的块"""
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
