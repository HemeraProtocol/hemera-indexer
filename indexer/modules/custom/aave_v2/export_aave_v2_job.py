import logging
from dataclasses import fields
from itertools import groupby
from operator import attrgetter

from web3 import Web3

from common.utils.format_utils import hex_str_to_bytes
from common.utils.web3_utils import extract_eth_address
from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.aave_v2 import constants
from indexer.modules.custom.aave_v2.abi.abi import abi_map
from indexer.modules.custom.aave_v2.domains.aave_v2_lending import (
    AaveV2LendingPool,
    AaveV2LendingPoolReserveFactorCurrent,
    AaveV2LendingPoolReserveFactorRecord, AaveV2DepositD, AaveV2WithdrawD, AaveV2BorrowD, AaveV2RepayD,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportAaveV2Job(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AaveV2LendingPool, AaveV2DepositD, AaveV2WithdrawD, AaveV2BorrowD, AaveV2RepayD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self.job_conf = self.user_defined_config
        self._create_reserve_topic0 = constants.RESERVE_INITIALIZED_TOPIC0
        self._change_factor_topic0 = constants.RESERVE_FACTOR_CHANGED_TOPIC0
        self.aave_lending_pool_v2_contract = self._web3.eth.contract(address=Web3.to_checksum_address(self.job_conf["POOL"]), abi=abi_map[self.job_conf["POOL"]])

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=['0x311bb771e4f8952e6da169b425e7e92d6ac45756', '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9']),
            ]
        )

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        res = []
        for lg in logs:
            if lg.address != '0x311bb771e4f8952e6da169b425e7e92d6ac45756':
                continue

            current_topic0 = lg.topic0
            if current_topic0 == self._create_reserve_topic0:
                self._collect_item(AaveV2LendingPool.type(), parse_init_reserve(lg))
            elif current_topic0 == '0xde6857219544bb5b7746f48ed30be6386fefc61b2f864cacf559893bf50fd951':
                topics = [hex_str_to_bytes(lg.get("topic" + str(i))) for i in range(4) if lg.get("topic" + str(i))]
                wlg = {
                    "address": lg.get("address"),
                    "topics": topics,
                    "data": hex_str_to_bytes(lg.get("data")),
                    "blockNumber": lg.get("block_number"),
                    "transactionHash": lg.get("transaction_hash"),
                    "transactionIndex": lg.get("transaction_index"),
                    "blockHash": lg.get("block_hash"),
                    "logIndex": lg.get("log_index"),
                    "removed": False,
                }
                dl = self.aave_lending_pool_v2_contract.events['Deposit']().process_log(wlg)
                tmp = AaveV2DepositD(
                    reserve=extract_eth_address(lg.topic1),
                    on_behalf_of=extract_eth_address(lg.topic2),
                    referral=lg.topic3,
                    user=dl.get("user"),
                    amount=dl.get("amount"),
                )
                res.append(tmp)
            # elif current_topic0 == self._change_factor_topic0:
            #     self._collect_item(
            #         AaveV2LendingPoolReserveFactorRecord.type(),
            #         AaveV2LendingPoolReserveFactorRecord(
            #             asset_address=common_utils.parse_hex_to_address(log.topic1),
            #             factor=common_utils.parse_hex_to_int256(log.data),
            #             block_number=log.block_number,
            #             block_timestamp=log.block_timestamp,
            #         ),
            #     )

        self._process_current_pool_data()
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
        reverse=common_utils.parse_hex_to_address(log.topic1),
        a_token_address=common_utils.parse_hex_to_address(log.topic2),
        stable_debt_token_address=address1,
        variable_debt_token_address=address2,
        interest_rate_strategy_address=address3,
        block_number=log.block_number,
        block_timestamp=log.block_timestamp,
    )
