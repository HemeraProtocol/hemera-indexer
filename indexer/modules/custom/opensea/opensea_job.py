import logging
from collections import defaultdict
from enum import Enum
from typing import List

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.opensea.domain.address_opensea_transactions import AddressOpenseaTransaction
from indexer.modules.custom.opensea.domain.opensea_order import OpenseaOrder
from indexer.modules.custom.opensea.parser.opensea_contract_parser import (
    OPENSEA_EVENT_ABI_SIGNATURE_MAPPING,
    OpenseaLog,
    parse_opensea_transaction_order_fulfilled_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

from collections import defaultdict


class OpenseaTransactionType(Enum):
    BUY = 0
    SELL = 1
    SWAP = 2


class ItemType(Enum):
    # 0: ETH on mainnet, MATIC on polygon, etc.
    NATIVE = 0
    # 1: ERC20 items (ERC777 and ERC20 analogues could also technically work)
    ERC20 = 1
    # 2: ERC721 items
    ERC721 = 2
    # 3: ERC1155 items
    ERC1155 = 3
    # 4: ERC721 items where a number of tokenIds are supported
    ERC721_WITH_CRITERIA = 4
    # 5: ERC1155 items where a number of ids are supported
    ERC1155_WITH_CRITERIA = 5


def get_opensea_transaction_type(offer, consideration):
    for item in offer:
        if item["itemType"] > 1:
            for item in consideration:
                if item["itemType"] > 1:
                    return OpenseaTransactionType.SWAP
                else:
                    return OpenseaTransactionType.SELL
        else:
            return OpenseaTransactionType.BUY
    return OpenseaTransactionType.SELL


def calculate_total_amount(consideration):
    total_amount = {}

    for item in consideration:
        token = item["token"]
        item_type = item["itemType"]
        amount = item["amount"]

        if token not in total_amount:
            total_amount[token] = {"type": item_type, "amount": {}}
            total_amount[token]["amount"][item_type] = amount
        else:
            total_amount[token]["amount"][item_type] += amount

    return total_amount


def calculate_fee_amount(consideration, seaport_fee_addresses):
    fee_amount = {}

    for item in consideration:
        recipient = item["recipient"]

        if recipient in seaport_fee_addresses:
            token = item["token"]
            item_type = item["itemType"]
            amount = item["amount"]

            if token not in fee_amount:
                fee_amount[token] = {"type": item_type, "amount": {}}
                fee_amount[token]["amount"][item_type] = amount
            else:
                fee_amount[token]["amount"][item_type] += amount

    return fee_amount


class OpenseaJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [AddressOpenseaTransaction, OpenseaOrder]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._seaport_1_6_config = self.user_defined_config.get("seaport_1_6", None)
        self._seaport_1_5_config = self.user_defined_config.get("seaport_1_5", None)

    def _collect(self, **kwargs):
        pass

    def transfer(self, opensea_logs: List[OpenseaLog]):
        for opensea_log in opensea_logs:
            yield OpenseaOrder(
                order_hash=opensea_log.orderHash,
                zone=opensea_log.zone,
                offerer=opensea_log.offerer,
                recipient=opensea_log.recipient,
                offer=opensea_log.offer,
                consideration=opensea_log.consideration,
                block_timestamp=opensea_log.block_timestamp,
                block_hash=opensea_log.block_hash,
                transaction_hash=opensea_log.transaction_hash,
                block_number=opensea_log.block_number,
                log_index=opensea_log.log_index,
                protocol_version=opensea_log.protocol_version,
            )
            offer = calculate_total_amount(opensea_log.offer)
            consideration = calculate_total_amount(opensea_log.consideration)
            fee = calculate_fee_amount(opensea_log.consideration, opensea_log.fee_addresses)

            opensea_transaciton_type = get_opensea_transaction_type(opensea_log.offer, opensea_log.consideration)

            yield AddressOpenseaTransaction(
                address=opensea_log.offerer,
                related_address=opensea_log.recipient,
                is_offer=True,
                transaction_type=opensea_transaciton_type.value,
                order_hash=opensea_log.orderHash,
                zone=opensea_log.zone,
                offer=offer,
                consideration=consideration,
                fee=fee,
                transaction_hash=opensea_log.transaction_hash,
                block_number=opensea_log.block_number,
                log_index=opensea_log.log_index,
                block_timestamp=opensea_log.block_timestamp,
                block_hash=opensea_log.block_hash,
                protocol_version=opensea_log.protocol_version,
            )
            yield AddressOpenseaTransaction(
                address=opensea_log.recipient,
                related_address=opensea_log.offerer,
                is_offer=False,
                transaction_type=(
                    1 - opensea_transaciton_type.value
                    if opensea_transaciton_type.value <= 1
                    else opensea_transaciton_type.value
                ),
                order_hash=opensea_log.orderHash,
                zone=opensea_log.zone,
                offer=offer,
                consideration=consideration,
                fee=fee,
                transaction_hash=opensea_log.transaction_hash,
                block_number=opensea_log.block_number,
                log_index=opensea_log.log_index,
                block_timestamp=opensea_log.block_timestamp,
                block_hash=opensea_log.block_hash,
                protocol_version=opensea_log.protocol_version,
            )

    def _process(self, **kwargs):
        transactions = self.get_filter_transactions()
        for transaction in transactions:
            orders = []
            if self._seaport_1_6_config:
                orders += parse_opensea_transaction_order_fulfilled_event(
                    transaction,
                    self._seaport_1_6_config["contract_address"],
                    protocol_version="1.6",
                    fee_addresses=self._seaport_1_6_config["fee_addresses"],
                )
            if self._seaport_1_5_config:
                orders += parse_opensea_transaction_order_fulfilled_event(
                    transaction,
                    self._seaport_1_5_config["contract_address"],
                    protocol_version="1.5",
                    fee_addresses=self._seaport_1_5_config.get("fee_addresses"),
                )
            self._collect_domains(self.transfer(orders))

    def get_filter(self):
        topic_filter_list = []
        if self._seaport_1_6_config:
            topic_filter_list.append(
                TopicSpecification(
                    addresses=[self._seaport_1_6_config["contract_address"]],
                    topics=list(OPENSEA_EVENT_ABI_SIGNATURE_MAPPING.values()),
                )
            )
        if self._seaport_1_5_config:
            topic_filter_list.append(
                TopicSpecification(
                    addresses=[self._seaport_1_5_config["contract_address"]],
                    topics=list(OPENSEA_EVENT_ABI_SIGNATURE_MAPPING.values()),
                )
            )

        return TransactionFilterByLogs(topic_filter_list)
