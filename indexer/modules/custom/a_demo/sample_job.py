#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Brief This job do the following things. Index
#
import logging
from collections import defaultdict
from typing import List

from eth_abi import abi
from sqlalchemy import func
from web3 import Web3

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.a_demo.domain.sample_domain import (
    ATransferD,
    SampleAddressCurrentD,
    sample_address_current_factory,
)
from indexer.modules.custom.a_demo.models.af_sample_address_current import SampleAddressCurrent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class SampleJob(FilterTransactionDataJob):
    # transaction with its logs
    dependency_types = [Transaction]
    output_types = [ATransferD, SampleAddressCurrentD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self.db_service = kwargs["config"].get("db_service")
        self.contract_address = "0xdac17f958d2ee523a2206206994597c13d831ec7"

    def get_filter(self):
        # usdt transfer
        topics = ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
        addresses = ["0xdac17f958d2ee523a2206206994597c13d831ec7"]
        return [
            TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)]),
        ]

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        res = []
        address_current_map = defaultdict(sample_address_current_factory)
        for transaction in transactions:
            address_current_map[transaction.from_address].transaction_count += 1
            address_current_map[transaction.to_address].transaction_count += 1
            logs = transaction.receipt.logs
            for log in logs:
                value = None
                try:
                    value = abi.decode(["uint256"], bytes.fromhex(log.data[2:]))[0]
                except ValueError:
                    logger.error("Failed to decode log %s", log.data)
                res.append(
                    ATransferD(
                        transaction_hash=transaction.hash,
                        log_index=log.log_index,
                        transaction_index=transaction.transaction_index,
                        block_number=transaction.block_number,
                        block_hash=transaction.block_hash,
                        block_timestamp=transaction.block_timestamp,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        transfer_from=extract_eth_address(log.topic1),
                        transfer_to=extract_eth_address(log.topic2),
                        value=value,
                    )
                )
        # group data by address
        for a_transfer in res:
            fr = address_current_map[a_transfer.from_address]
            fr.address = a_transfer.from_address
            fr.transfer_from_count += 1
            fr.transfer_from_value += a_transfer.value
            fr.block_number = a_transfer.block_number

            to = address_current_map[a_transfer.to_address]
            to.address = a_transfer.to_address
            to.transfer_to_count += 1
            to.transfer_to_value += a_transfer.value
            to.block_number = a_transfer.block_number

        self._collect_items(ATransferD.type(), res)
        # fetch exists
        exists_address_current = self.get_existing_transfers(list(address_current_map.keys()))
        for address, address_current in address_current_map.items():
            if address in exists_address_current:
                # if exists, merge data
                exists_data = exists_address_current[address]
                exists_data.transaction_count += address_current.transaction_count
                exists_data.transfer_from_count += address_current.transfer_from_count
                exists_data.transfer_from_value += address_current.transfer_from_value
                exists_data.transfer_to_count += address_current.transfer_to_count
                exists_data.transfer_to_value += address_current.transfer_to_value
                exists_data.block_number = address_current.block_number
                self._collect_item(exists_data.type(), exists_data)
            else:
                self._collect_item(address_current.type(), address_current)

    def get_existing_transfers(self, addresses):
        if not self.db_service:
            return {}
        addresses = [ad[2:] for ad in addresses if ad.startswith("0x")]

        with self.db_service.get_service_session() as session:
            query = session.query(SampleAddressCurrent).filter(
                func.encode(SampleAddressCurrent.address, "hex").in_(addresses)
            )
            result = query.all()

        return {
            f"{'0x' + row.address.hex()}": SampleAddressCurrentD(
                address=row.address,
                transaction_count=row.transaction_count,
                transfer_from_count=row.transfer_from_count,
                transfer_from_value=row.transfer_from_value,
                transfer_to_count=row.transfer_to_count,
                transfer_to_value=row.transfer_to_value,
                block_number=row.block_number,
            )
            for row in result
        }


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()
