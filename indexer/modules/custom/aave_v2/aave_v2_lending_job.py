import configparser
import json
import logging
import os
from collections import defaultdict
from dataclasses import fields
from itertools import groupby
from operator import attrgetter
from typing import Dict, List

import eth_abi
from web3 import Web3

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.aave_v2 import constants
from indexer.modules.custom.aave_v2.domain.aave_v2_lending import (
    AaveV2LendingPool,
    AaveV2LendingPoolReserveFactorCurrent,
    AaveV2LendingPoolReserveFactorRecord,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)


class AaveV2LendingPoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AaveV2LendingPool, AaveV2LendingPoolReserveFactorCurrent, AaveV2LendingPoolReserveFactorRecord]
    able_to_reorg = True

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
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self._create_reserve_topic0 = constants.RESERVE_INITIALIZED_TOPIC0
        self._change_factor_topic0 = constants.RESERVE_FACTOR_CHANGED_TOPIC0

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._lending_configurator_address]),
            ]
        )

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)
        chain_id_str = str(chain_id)
        try:
            chain_config = config[chain_id_str]
        except KeyError:
            return
        try:
            self._lending_configurator_address = chain_config.get("lending_pool_configurator_v2").lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        self._batch_work_executor.execute(logs, self._collect_batch, len(logs))
        self._batch_work_executor.wait()

        self._process_current_pool_data()

    def _collect_batch(self, logs):

        for log in logs:
            if log.address != self._lending_configurator_address:
                continue

            current_topic0 = log.topic0
            if current_topic0 == self._create_reserve_topic0:
                self._collect_item(AaveV2LendingPool.type(), parse_init_reserve(log))
            elif current_topic0 == self._change_factor_topic0:
                self._collect_item(
                    AaveV2LendingPoolReserveFactorRecord.type(),
                    AaveV2LendingPoolReserveFactorRecord(
                        asset_address=common_utils.parse_hex_to_address(log.topic1),
                        factor=common_utils.parse_hex_to_int256(log.data),
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                    ),
                )

    def _process(self, **kwargs):
        self._data_buff[AaveV2LendingPool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[AaveV2LendingPoolReserveFactorRecord.type()].sort(key=lambda x: x.block_number)
        self._data_buff[AaveV2LendingPoolReserveFactorCurrent.type()].sort(key=lambda x: x.block_number)

    def _process_current_pool_data(self):
        records = self._data_buff[AaveV2LendingPoolReserveFactorRecord.type()]
        self._data_buff[AaveV2LendingPoolReserveFactorRecord.type()] = []
        unique_records = {}
        for record in records:
            key = (record.asset_address, record.block_number)
            unique_records[key] = record

        for price in unique_records.values():
            self._collect_item(AaveV2LendingPoolReserveFactorRecord.type(), price)

        sorted_records = sorted(unique_records.values(), key=lambda x: (x.asset_address, x.block_number))
        current_records = [
            max(group, key=attrgetter("block_number"))
            for _, group in groupby(sorted_records, key=attrgetter("asset_address"))
        ]
        for data in current_records:
            self._collect_item(AaveV2LendingPoolReserveFactorCurrent.type(), self.create_current_status(data))

    @staticmethod
    def create_current_status(detail: AaveV2LendingPoolReserveFactorRecord) -> AaveV2LendingPoolReserveFactorCurrent:
        return AaveV2LendingPoolReserveFactorCurrent(
            **{field.name: getattr(detail, field.name) for field in fields(AaveV2LendingPoolReserveFactorRecord)}
        )


def split_three_address_from_hex(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]
    part1 = hex_string[:64]
    part2 = hex_string[64:128]
    part3 = hex_string[128:192]
    return (
        common_utils.parse_hex_to_address(part1),
        common_utils.parse_hex_to_address(part2),
        common_utils.parse_hex_to_address(part3),
    )


def parse_init_reserve(log):
    address1, address2, address3 = split_three_address_from_hex(log.data)
    return AaveV2LendingPool(
        asset_address=common_utils.parse_hex_to_address(log.topic1),
        a_token_address=common_utils.parse_hex_to_address(log.topic2),
        stable_debt_token_address=address1,
        variable_debt_token_address=address2,
        interest_rate_strategy_address=address3,
        block_number=log.block_number,
        block_timestamp=log.block_timestamp,
    )
