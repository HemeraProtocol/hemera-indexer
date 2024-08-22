import configparser
import json
import logging
import os
import threading
from collections import defaultdict

from indexer.domain.block import Block
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordBlueChipHolders
from indexer.modules.custom.blue_chip import constants
from indexer.modules.custom.blue_chip.domain.feature_blue_chip import BlueChipHolder
from indexer.modules.custom.blue_chip.models.feature_blue_chip_holders import FeatureBlueChipHolders
from indexer.modules.custom.feature_type import FeatureType
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.BLUE_CHIP_HOLDING.value


class ExportBlueChipHoldersJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, Block]
    output_types = [AllFeatureValueRecordBlueChipHolders, BlueChipHolder]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = (kwargs.get("config", {}).get("db_service"),) if kwargs.get("config") is not None else None
        self._blue_chip_projects = constants.BLUE_CHIP_PROJECTS
        self._current_holders = self.get_current_holders(self._service)
        self._updates_this_batch = {}

    def get_filter(self):
        return TransactionFilterByLogs([TopicSpecification(addresses=self._blue_chip_projects)])

    def _collect(self, **kwargs):
        token_balance = self._data_buff[TokenBalance.type()]
        if token_balance is None or len(token_balance) == 0:
            return
        self._batch_work_executor.execute(
            token_balance,
            self._collect_batch,
            total_items=len(token_balance),
            split_method=split_token_balances,
        )

        self._batch_work_executor.wait()

    def _collect_batch(self, token_balances):
        block_dict = {}
        for address, token_balance_list in token_balances.items():
            for token_balance in token_balance_list:

                token_address = token_balance.token_address
                if token_address not in self._blue_chip_projects:
                    continue

                wallet_address = token_balance.address
                balance = token_balance.balance
                block_number = token_balance.block_number

                if wallet_address not in block_dict:
                    block_dict[wallet_address] = {}
                if block_number not in block_dict[wallet_address]:
                    block_dict[wallet_address][block_number] = {}

                block_dict[wallet_address][block_number][token_address] = balance

            for wallet_address, blocks in block_dict.items():
                updated = False

                if wallet_address not in self._current_holders:
                    self._current_holders[wallet_address] = {}
                    self._updates_this_batch[wallet_address] = {}
                else:
                    self._updates_this_batch[wallet_address] = self._current_holders[wallet_address]

                records = self.convert_holding_to_records(FEATURE_ID, wallet_address, blocks)
                for record in records:
                    self._collect_item(AllFeatureValueRecordBlueChipHolders.type(), record)

                latest_balances = {}
                for block_number, tokens in blocks.items():
                    for token_address, balance in tokens.items():
                        if token_address not in latest_balances or block_number > latest_balances[token_address][0]:
                            latest_balances[token_address] = (block_number, balance)

                for token_address, (block_num, balance) in latest_balances.items():
                    self._current_holders[wallet_address][token_address] = balance
                    self._updates_this_batch[wallet_address][token_address] = balance

    def _process(self, **kwargs):
        # collect _updates_this_batch
        self._collect_current_holding()
        self._data_buff[BlueChipHolder.type()].sort(key=lambda x: x.block_number)
        self._data_buff[AllFeatureValueRecordBlueChipHolders.type()].sort(key=lambda x: x.block_number)
        self._updates_this_batch = {}

    @staticmethod
    def get_current_holders(db_service):
        if not db_service:
            return {}

        session = db_service[0].get_service_session()
        try:
            result = session.query(FeatureBlueChipHolders).all()
            history_dict = {}
            if result is not None:
                for item in result:
                    wallet_address = "0x" + item.wallet_address.hex()
                    history_dict[wallet_address] = item.hold_detail

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return history_dict

    @staticmethod
    def convert_holding_to_records(feature_id, wallet_address, blocks_data):
        result = []
        for block_number, data in blocks_data.items():
            result.append(
                AllFeatureValueRecordBlueChipHolders(
                    feature_id=feature_id,
                    block_number=block_number,
                    address=wallet_address,
                    value=data,
                )
            )
        return result

    def _collect_current_holding(self):
        blocks = self._data_buff[Block.type()]
        if blocks is None or len(blocks) == 0:
            return
        last_block = blocks[-1]

        for wallet_address, data in self._updates_this_batch.items():
            holding_count = sum(count for _, count in data.items())
            self._collect_item(
                BlueChipHolder.type(),
                BlueChipHolder(
                    wallet_address=wallet_address,
                    hold_detail=data,
                    current_count=holding_count,
                    block_number=last_block.block_number,
                    block_timestamp=last_block.timestamp,
                ),
            )


def split_token_balances(token_balances):
    token_balance_dict = defaultdict(list)
    for data in token_balances:
        token_balance_dict[data.address].append(data)

    for address, data in token_balance_dict.items():
        yield {address: data}
