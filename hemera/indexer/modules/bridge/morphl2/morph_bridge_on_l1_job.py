import logging

from hemera.indexer.domain.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.modules.bridge.domain.morph import MorphDepositedTransactionOnL1, MorphWithdrawalTransactionOnL1
from hemera.indexer.modules.bridge.morphl2.abi.event import QueueTransactionEvent, RelayedMessageEvent
from hemera.indexer.modules.bridge.morphl2.parser.parser import (
    parse_relayed_message_event,
    parse_transaction_deposited_event,
)
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class MorphBridgeOnL1Job(FilterTransactionDataJob):
    is_locked = True
    dependency_types = [Transaction]
    output_types = [
        MorphDepositedTransactionOnL1,
        MorphWithdrawalTransactionOnL1,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.l1_message_queue_oracle_contract_address = self.user_defined_config.get(
            "l1_message_queue_oracle_contract_address"
        )
        self.l1_cross_domain_messenger_contract_address = self.user_defined_config.get(
            "l1_cross_domain_messenger_contract_address"
        )

    def get_filter(self):
        filter_list = []
        if self.l1_message_queue_oracle_contract_address:
            filter_list.append(
                TopicSpecification(
                    addresses=[self.l1_message_queue_oracle_contract_address],
                    topics=[QueueTransactionEvent.get_signature()],
                )
            )
        if self.l1_cross_domain_messenger_contract_address:
            filter_list.append(
                TopicSpecification(
                    addresses=[self.l1_cross_domain_messenger_contract_address],
                    topics=[RelayedMessageEvent.get_signature()],
                )
            )

        return TransactionFilterByLogs(filter_list)

    def _process(self, **kwargs):
        transactions = self.get_filter_transactions()
        deposited_transactions = []
        relayed_message_transactions = []
        for transaction in transactions:
            if self.l1_message_queue_oracle_contract_address:
                deposited_transactions += parse_transaction_deposited_event(
                    transaction, self.l1_message_queue_oracle_contract_address
                )
            if self.l1_cross_domain_messenger_contract_address:
                relayed_message_transactions += parse_relayed_message_event(
                    transaction, self.l1_cross_domain_messenger_contract_address
                )

        for deposited_transaction in deposited_transactions:
            self._collect_domain(
                MorphDepositedTransactionOnL1(
                    msg_hash=deposited_transaction.msg_hash,
                    version=deposited_transaction.version,
                    index=deposited_transaction.index,
                    l1_block_number=deposited_transaction.block_number,
                    l1_block_timestamp=deposited_transaction.block_timestamp,
                    l1_block_hash=deposited_transaction.block_hash,
                    l1_transaction_hash=deposited_transaction.transaction_hash,
                    l1_from_address=deposited_transaction.from_address,
                    l1_to_address=deposited_transaction.to_address,
                    l1_token_address=deposited_transaction.remote_token_address,
                    l2_token_address=deposited_transaction.local_token_address,
                    from_address=deposited_transaction.bridge_from_address,
                    to_address=deposited_transaction.bridge_to_address,
                    amount=deposited_transaction.amount,
                    extra_info=deposited_transaction.extra_info,
                    _type=deposited_transaction._type,
                    sender=deposited_transaction.sender,
                    target=deposited_transaction.target,
                    data=deposited_transaction.data,
                )
            )

        for relayed_message_transaction in relayed_message_transactions:
            self._collect_domain(
                MorphWithdrawalTransactionOnL1(
                    msg_hash=relayed_message_transaction.msg_hash,
                    l1_block_number=relayed_message_transaction.block_number,
                    l1_block_timestamp=relayed_message_transaction.block_timestamp,
                    l1_block_hash=relayed_message_transaction.block_hash,
                    l1_transaction_hash=relayed_message_transaction.transaction_hash,
                    l1_from_address=relayed_message_transaction.from_address,
                    l1_to_address=relayed_message_transaction.to_address,
                )
            )
