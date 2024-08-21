import configparser
import json
import logging
import os
import threading
from collections import defaultdict
from queue import Queue
from typing import List, cast

import eth_abi
from web3.types import ABIEvent

from common import models
from indexer.domain import dict_to_dataclass
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.merchant_moe import constants
from indexer.modules.custom.merchant_moe.domain.erc1155_token_holding import (
    MerchantMoeErc1155TokenCurrentHolding,
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenHolding,
    MerchantMoeErc1155TokenSupply,
)
from indexer.modules.custom.merchant_moe.domain.merchant_moe import MerChantMoeTokenBin, MerChantMoeTokenCurrentBin
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.MERCHANT_MOE_1155_LIQUIDITY.value


class ExportMerchantMoe1155LiquidityJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance]
    output_types = [
        MerchantMoeErc1155TokenHolding,
        MerchantMoeErc1155TokenCurrentHolding,
        MerchantMoeErc1155TokenSupply,
        MerchantMoeErc1155TokenCurrentSupply,
        MerChantMoeTokenBin,
        MerChantMoeTokenCurrentBin,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self._need_collected_list),
            ]
        )

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            address_list_str = config.get(str(chain_id), "address_list")
            self._need_collected_list = address_list_str.split(",")
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        if self._need_collected_list is None or len(self._need_collected_list) == 0:
            return
        token_balances = self._data_buff[TokenBalance.type()]
        if token_balances is None or len(token_balances) == 0:
            return
        self._batch_work_executor.execute(
            token_balances, self._collect_batch, total_items=len(token_balances), split_method=split_token_balances
        )

        self._batch_work_executor.wait()

    def _collect_batch(self, token_balances) -> None:
        if token_balances is None or len(token_balances) == 0:
            return
        token_address = next(iter(token_balances))
        if token_address not in self._need_collected_list:
            return
        need_call_list = []
        current_token_holding = {}
        for token_balance in token_balances[token_address]:
            token_address = token_balance.token_address
            block_number = token_balance.block_number
            block_timestamp = token_balance.block_timestamp
            token_id = token_balance.token_id
            need_call_list.append(
                {
                    "block_number": block_number,
                    "block_timestamp": block_timestamp,
                    "token_id": token_id,
                }
            )
            self._collect_item(MerchantMoeErc1155TokenHolding.type(), parse_balance_to_holding(token_balance))

            key = token_id
            if key not in current_token_holding or block_number > current_token_holding[key].block_number:
                current_token_holding[key] = MerchantMoeErc1155TokenCurrentHolding(
                    token_address=token_balance.token_address,
                    wallet_address=token_balance.address,
                    token_id=token_id,
                    balance=token_balance.balance,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )
        for data in current_token_holding.values():
            self._collect_item(MerchantMoeErc1155TokenCurrentHolding.type(), data)

        total_supply_dtos = batch_get_total_supply(
            self._web3,
            self._batch_web3_provider.make_request,
            need_call_list,
            token_address,
            self._is_batch,
            constants.ABI_LIST,
        )
        total_bin_dtos = batch_get_bin(
            self._web3,
            self._batch_web3_provider.make_request,
            need_call_list,
            token_address,
            self._is_batch,
            constants.ABI_LIST,
        )
        current_total_supply_dict = {}
        current_token_bin_dict = {}
        for data in total_bin_dtos:
            token_id = data["token_id"]
            block_number = data["block_number"]
            block_timestamp = data["block_timestamp"]
            total_supply = data["totalSupply"]
            reserve0_bin = data["reserve0_bin"]
            reserve1_bin = data["reserve1_bin"]
            common_token_data = {
                "token_address": token_address,
                "token_id": token_id,
            }
            common_current_block_data = {
                "block_number": block_number,
                "block_timestamp": block_timestamp,
            }
            common_record_block_data = {
                "called_block_number": block_number,
                "called_block_timestamp": block_timestamp,
            }

            key = token_id
            if key not in current_total_supply_dict or block_number > current_total_supply_dict[key].block_number:
                current_total_supply_dict[key] = MerchantMoeErc1155TokenCurrentSupply(
                    **common_token_data,
                    **common_current_block_data,
                    total_supply=total_supply,
                )
            if key not in current_token_bin_dict or block_number > current_token_bin_dict[key].block_number:
                current_token_bin_dict[key] = MerChantMoeTokenCurrentBin(
                    **common_token_data,
                    **common_current_block_data,
                    reserve0_bin=reserve0_bin,
                    reserve1_bin=reserve1_bin,
                )
            self._collect_item(
                MerchantMoeErc1155TokenSupply.type(),
                MerchantMoeErc1155TokenSupply(
                    **common_token_data,
                    **common_record_block_data,
                    total_supply=total_supply,
                ),
            )
            self._collect_item(
                MerChantMoeTokenBin.type(),
                MerChantMoeTokenBin(
                    **common_token_data,
                    **common_record_block_data,
                    reserve0_bin=reserve0_bin,
                    reserve1_bin=reserve1_bin,
                ),
            )
        for data in current_total_supply_dict.values():
            self._collect_item(MerchantMoeErc1155TokenCurrentSupply.type(), data)
        for data in current_token_bin_dict.values():
            self._collect_item(MerChantMoeTokenCurrentBin.type(), data)

    def _process(self):

        self._data_buff[MerchantMoeErc1155TokenHolding.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[MerchantMoeErc1155TokenSupply.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[MerChantMoeTokenBin.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[MerchantMoeErc1155TokenCurrentSupply.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoeTokenCurrentBin.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerchantMoeErc1155TokenCurrentHolding.type()].sort(key=lambda x: x.block_number)


def parse_balance_to_holding(token_balance: TokenBalance):
    return MerchantMoeErc1155TokenHolding(
        token_address=token_balance.token_address,
        wallet_address=token_balance.address,
        token_id=token_balance.token_id,
        balance=token_balance.balance,
        called_block_number=token_balance.block_number,
        called_block_timestamp=token_balance.block_timestamp,
    )


def split_token_balances(token_balances):
    token_balance_dict = defaultdict(list)
    for data in token_balances:
        token_balance_dict[data.token_address].append(data)

    for token_address, data in token_balance_dict.items():
        yield {token_address: data}


def batch_get_bin(web3, make_requests, requests, nft_address, is_batch, abi_list):
    fn_name = "getBin"
    if len(requests) == 0:
        return []
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_one_input_one_output_method_data(web3, requests, nft_address, fn_name, abi_list)

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token["reserve0_bin"] = decoded_data[0]
            token["reserve1_bin"] = decoded_data[1]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def batch_get_total_supply(web3, make_requests, requests, nft_address, is_batch, abi_list):
    fn_name = "totalSupply"
    if len(requests) == 0:
        return []
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_one_input_one_output_method_data(web3, requests, nft_address, fn_name, abi_list)

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token[fn_name] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos
