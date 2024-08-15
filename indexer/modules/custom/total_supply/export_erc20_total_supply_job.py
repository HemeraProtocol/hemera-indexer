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
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordErc20TotalSupply
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.total_supply import constants
from indexer.modules.custom.total_supply.domain.erc20_total_supply import Erc20TotalSupply
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.ERC20_TOTAL_SUPPLY.value


class ExportUniSwapV2InfoJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [AllFeatureValueRecordErc20TotalSupply, Erc20TotalSupply]

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
        token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        # filter and group
        if token_transfers is None or len(token_transfers) == 0:
            return
        self._batch_work_executor.execute(
            token_transfers,
            self._collect_batch,
            total_items=len(token_transfers),
            split_method=split_token_transfers,
        )

        self._batch_work_executor.wait()

    def _collect_batch(self, token_transfers) -> None:
        if token_transfers is None or len(token_transfers) == 0:
            return
        token_address = next(iter(token_transfers))
        if token_address not in self._need_collected_list:
            return
        grouped_block = {}

        for entity in token_transfers[token_address]:
            grouped_block[entity.block_number] = entity.block_timestamp

        # collect total supply
        total_supply_infos = collect_pool_total_supply(
            list(grouped_block.keys()),
            token_address,
            constants.ABI,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
        )
        for data in total_supply_infos:
            block_number = data["block_number"]
            block_timestamp = grouped_block[block_number]
            total_supply = data["totalSupply"]
            self._collect_item(
                AllFeatureValueRecordErc20TotalSupply.type(),
                parse_to_record(FEATURE_ID, block_number, block_timestamp, token_address, total_supply),
            )

            self._collect_item(
                Erc20TotalSupply.type(),
                parse_to_total_supply(block_number, block_timestamp, token_address, total_supply),
            )

    def _process(self):

        self._data_buff[Erc20TotalSupply.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[AllFeatureValueRecordErc20TotalSupply.type()].sort(key=lambda x: x.block_number)


def parse_to_record(feature_id, block_number, block_timestamp, address, total_supply):
    value = {
        "total_supply": total_supply,
        "block_number": block_number,
        "block_timestamp": block_timestamp,
    }
    return AllFeatureValueRecordErc20TotalSupply(
        feature_id=feature_id,
        block_number=block_number,
        address=address,
        value=value,
    )


def parse_to_total_supply(block_number, block_timestamp, address, total_supply):
    return Erc20TotalSupply(
        token_address=address,
        total_supply=total_supply,
        called_block_number=block_number,
        called_block_timestamp=block_timestamp,
    )


def collect_pool_total_supply(block_number_set, contract_address, abi_list, web3, make_requests, is_batch):
    need_collect_list = []
    for block_number in block_number_set:
        need_collect_list.append({"address": contract_address, "block_number": block_number})

    # call totalSupply
    total_supply_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, need_collect_list, is_batch, abi_list, "totalSupply", "address"
    )

    return total_supply_infos


def split_token_transfers(token_transfers):
    token_transfer_dict = defaultdict(list)
    for data in token_transfers:
        token_transfer_dict[data.token_address].append(data)

    for token_address, data in token_transfer_dict.items():
        yield {token_address: data}
