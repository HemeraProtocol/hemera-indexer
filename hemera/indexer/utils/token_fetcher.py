#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/7 13:44
# @Author  will
# @File  token_fetcher.py
# @Brief use the `multicall` contract to fetch data

import logging

from hemera.common.enumeration.record_level import RecordLevel
from hemera.common.enumeration.token_type import TokenType
from hemera.common.utils.format_utils import to_snake_case
from hemera.indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from hemera.indexer.utils.abi_setting import (
    ERC20_BALANCE_OF_FUNCTION,
    ERC721_OWNER_OF_FUNCTION,
    ERC721_TOKEN_URI_FUNCTION,
    ERC1155_MULTIPLE_TOKEN_URI_FUNCTION,
    ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION,
    TOKEN_TOTAL_SUPPLY_WITH_ID_FUNCTION,
)
from hemera.indexer.utils.exception_recorder import ExceptionRecorder
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera.indexer.utils.multicall_hemera.util import calculate_execution_time

exception_recorder = ExceptionRecorder()


class TokenFetcher:

    def __init__(self, web3, kwargs=None, logger=None):
        if not logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.multi_call_helper = MultiCallHelper(web3, kwargs, logger)

        self.token_k_fields = ("address", "token_address", "block_number", "token_type", "token_id")
        self.token_ids_infos_k_fields = ("address", "token_id", "token_type", "is_get_token_uri")

        self.fixed_k = "__k"

    @calculate_execution_time
    def _prepare_token_ids_info_parameters(self, token_info_items):
        calls = []
        cnt = 0
        for row in token_info_items:
            row[self.fixed_k] = cnt
            cnt += 1

            construct_call = None
            address = row["address"]
            block_number = row["block_number"]
            if row["token_type"] == TokenType.ERC721.value:
                if row["is_get_token_uri"] is True:
                    construct_call = Call(
                        target=address,
                        function_abi=ERC721_TOKEN_URI_FUNCTION,
                        parameters=[row["token_id"]],
                        block_number=block_number,
                        user_defined_k=row[self.fixed_k],
                    )
                else:
                    construct_call = Call(
                        target=address,
                        function_abi=ERC721_OWNER_OF_FUNCTION,
                        parameters=[row["token_id"]],
                        block_number=block_number,
                        user_defined_k=row[self.fixed_k],
                    )
            elif row["token_type"] == TokenType.ERC1155.value:
                if row["is_get_token_uri"] is True:
                    construct_call = Call(
                        target=address,
                        function_abi=ERC1155_MULTIPLE_TOKEN_URI_FUNCTION,
                        parameters=[row["token_id"]],
                        block_number=block_number,
                        user_defined_k=row[self.fixed_k],
                    )

                # else:
                #     construct_call = Call(
                #         target=address,
                #         function_abi=TOKEN_TOTAL_SUPPLY_WITH_ID_FUNCTION,
                #         parameters=[row["token_id"]],
                #         block_number=block_number,
                #         user_defined_k=row[self.fixed_k],
                #     )

            if construct_call:
                calls.append(construct_call)
        return calls

    def create_token_detail(self, token_info, value):
        common_args = {
            "token_address": token_info["address"],
            "token_id": token_info["token_id"],
            "block_number": token_info["block_number"],
            "block_timestamp": token_info["block_timestamp"],
        }
        try:

            if token_info["is_get_token_uri"]:
                try:
                    token_uri = value.get("uri")
                except Exception as e:
                    token_uri = None
                    logging.debug(f"decode token uri failed, token_info={token_info}, value={value}")
                if token_info["token_type"] == "ERC721":
                    return [ERC721TokenIdDetail(**common_args, token_uri=token_uri)]
                else:
                    return [ERC1155TokenIdDetail(**common_args, token_uri=token_uri)]
            else:
                if token_info["token_type"] == "ERC721":
                    token_owner = value.get("owner")
                    return [
                        UpdateERC721TokenIdDetail(**common_args, token_owner=token_owner),
                        ERC721TokenIdChange(**common_args, token_owner=token_owner),
                    ]
                else:
                    total_supply = value.get("totalSupply")
                    return [UpdateERC1155TokenIdDetail(**common_args, token_supply=total_supply)]
        except Exception as e:
            exception_recorder.log(
                block_number=token_info["block_number"],
                dataclass=to_snake_case("token_id_info"),
                message_type="decode_token_id_info_fail",
                message=str(e),
                exception_env=token_info,
                level=RecordLevel.WARN,
            )

    @calculate_execution_time
    def fetch_token_ids_info(self, token_info_items):
        # export token_ids_info
        self.logger.info(f"TokenFetcher fetch_token_ids_info size={len(token_info_items)}")
        calls = self._prepare_token_ids_info_parameters(token_info_items)
        self.multi_call_helper.execute_calls(calls)

        multicall_result = {call.user_defined_k: call.returns for call in calls}
        return_data = []

        for token_info in token_info_items:
            bk = token_info[self.fixed_k]
            value = multicall_result[bk]
            tmp = self.create_token_detail(token_info, value)
            if tmp:
                return_data.extend(tmp)
        return return_data

    @calculate_execution_time
    def _prepare_token_balance_parameters(self, tokens):
        calls = []
        cnt = 0
        for row in tokens:
            row[self.fixed_k] = cnt
            cnt += 1

            token, wal = row["token_address"], row["address"]
            token_id = row["token_id"]
            token_type = row["token_type"]
            block_number = row["block_number"]
            if token_type == "ERC1155" and token_id is not None:
                construct_call = Call(
                    target=token,
                    function_abi=ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION,
                    parameters=[wal, token_id],
                    block_number=block_number,
                    user_defined_k=row[self.fixed_k],
                )
            else:
                construct_call = Call(
                    target=token,
                    function_abi=ERC20_BALANCE_OF_FUNCTION,
                    parameters=[wal],
                    block_number=block_number,
                    user_defined_k=row[self.fixed_k],
                )
            if construct_call:
                calls.append(construct_call)
        return calls

    @calculate_execution_time
    def fetch_token_balance(self, tokens):
        self.logger.info(f"TokenFetcher fetch_token_balance size={len(tokens)}")
        calls = self._prepare_token_balance_parameters(tokens)
        self.multi_call_helper.execute_calls(calls)

        multicall_result = {call.user_defined_k: call.returns for call in calls}
        return_data = []
        for item in tokens:
            bk = item[self.fixed_k]
            balance = None
            if bk in multicall_result and multicall_result[bk]:
                balance = multicall_result[bk]["balance"]
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
