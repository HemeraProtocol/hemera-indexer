import logging

from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera_udf.bridge.domains.morph import MorphDepositedTransactionOnL2, MorphWithdrawalTransactionOnL2
from hemera_udf.bridge.morphl2.abi.event import RelayedMessageEvent, SentMessageEvent
from hemera_udf.bridge.morphl2.parser.parser import parse_relayed_message_event, parse_sent_message_event

logger = logging.getLogger(__name__)


class MorphBridgeOnL2Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [
        MorphDepositedTransactionOnL2,
        MorphWithdrawalTransactionOnL2,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.l2_cross_domain_messenger_contract_address = self.user_defined_config.get(
            "l2_cross_domain_messenger_contract_address"
        )

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[self.l2_cross_domain_messenger_contract_address],
                    topics=[RelayedMessageEvent.get_signature(), SentMessageEvent.get_signature()],
                )
            ]
        )

    def _process(self, **kwargs):
        transactions = self.get_filter_transactions()
        deposited_transactions = []
        relayed_message_transactions = []
        for transaction in transactions:
            deposited_transactions += parse_sent_message_event(
                transaction, self.l2_cross_domain_messenger_contract_address
            )
            relayed_message_transactions += parse_relayed_message_event(
                transaction, self.l2_cross_domain_messenger_contract_address
            )

        for deposited_transaction in deposited_transactions:
            self._collect_domain(
                MorphWithdrawalTransactionOnL2(
                    msg_hash=deposited_transaction.msg_hash,
                    version=deposited_transaction.version,
                    index=deposited_transaction.index,
                    l2_block_number=deposited_transaction.block_number,
                    l2_block_timestamp=deposited_transaction.block_timestamp,
                    l2_block_hash=deposited_transaction.block_hash,
                    l2_transaction_hash=deposited_transaction.transaction_hash,
                    l2_from_address=deposited_transaction.from_address,
                    l2_to_address=deposited_transaction.to_address,
                    amount=deposited_transaction.amount,
                    from_address=deposited_transaction.bridge_from_address,
                    to_address=deposited_transaction.bridge_to_address,
                    l1_token_address=deposited_transaction.remote_token_address,
                    l2_token_address=deposited_transaction.local_token_address,
                    extra_info=deposited_transaction.extra_info,
                    _type=deposited_transaction._type,
                    sender=deposited_transaction.sender,
                    target=deposited_transaction.target,
                    data=deposited_transaction.data,
                )
            )

        for relayed_message_transaction in relayed_message_transactions:
            self._collect_domain(
                MorphDepositedTransactionOnL2(
                    msg_hash=relayed_message_transaction.msg_hash,
                    l2_block_number=relayed_message_transaction.block_number,
                    l2_block_timestamp=relayed_message_transaction.block_timestamp,
                    l2_block_hash=relayed_message_transaction.block_hash,
                    l2_transaction_hash=relayed_message_transaction.transaction_hash,
                    l2_from_address=relayed_message_transaction.from_address,
                    l2_to_address=relayed_message_transaction.to_address,
                )
            )
