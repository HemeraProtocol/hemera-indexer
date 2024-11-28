import logging

from common.utils.exception_control import FastShutdownError
from custom_jobs.bridge.bedrock.parser.bedrock_bridge_parser import (
    BEDROCK_EVENT_ABI_SIGNATURE_MAPPING,
    parse_message_passed_event,
    parse_relayed_message,
)
from custom_jobs.bridge.domains.op_bedrock import *
from indexer.domains.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class BedrockBridgeOnL2Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [
        OpL2ToL1WithdrawnTransactionOnL2,
        OpL1ToL2DepositedTransactionOnL2,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"]

        self._l2_to_l1_message_passer = config.get("l2_to_l1_message_passer")
        self._l2_cross_domain_messenger = config.get("l2_cross_domain_messenger")

        if self._l2_to_l1_message_passer is None or self._l2_cross_domain_messenger is None:
            raise FastShutdownError("Both l2_to_l1_message_passer and l2_cross_domain_messenger must be provided.")

    def get_filter(self):
        topics = [
            BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["RELAYED_MESSAGE_EVENT"],
            BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["MESSAGE_PASSED_EVENT"],
        ]
        addresses = [self._l2_to_l1_message_passer, self._l2_cross_domain_messenger]

        return TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)])

    def _process(self, **kwargs):
        # filter out transactions that are not bridge related
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []
        result.extend(
            [
                OpL1ToL2DepositedTransactionOnL2(
                    msg_hash=relay_transaction.msg_hash,
                    l2_block_number=relay_transaction.block_number,
                    l2_block_timestamp=relay_transaction.block_timestamp,
                    l2_block_hash=relay_transaction.block_hash,
                    l2_transaction_hash=relay_transaction.transaction_hash,
                    l2_from_address=relay_transaction.from_address,
                    l2_to_address=relay_transaction.to_address,
                )
                for transaction in transactions
                for relay_transaction in parse_relayed_message(
                    "RELAYED_MESSAGE_EVENT",
                    transaction,
                    self._l2_cross_domain_messenger,
                    "msgHash",
                )
            ]
        )

        result.extend(
            [
                OpL2ToL1WithdrawnTransactionOnL2(
                    msg_hash=withdrawn_transaction.withdrawal_hash,
                    version=withdrawn_transaction.version,
                    index=withdrawn_transaction.index,
                    l2_block_number=withdrawn_transaction.block_number,
                    l2_block_timestamp=withdrawn_transaction.block_timestamp,
                    l2_block_hash=withdrawn_transaction.block_hash,
                    l2_transaction_hash=withdrawn_transaction.transaction_hash,
                    l2_from_address=withdrawn_transaction.from_address,
                    l2_to_address=withdrawn_transaction.to_address,
                    amount=withdrawn_transaction.amount,
                    from_address=withdrawn_transaction.bridge_from_address,
                    to_address=withdrawn_transaction.bridge_to_address,
                    l1_token_address=withdrawn_transaction.local_token_address,
                    l2_token_address=withdrawn_transaction.remote_token_address,
                    extra_info=withdrawn_transaction.extra_info,
                    _type=withdrawn_transaction.bridge_transaction_type,
                    target=withdrawn_transaction.target,
                    sender=withdrawn_transaction.sender,
                    data=withdrawn_transaction.message,
                )
                for transaction in transactions
                for withdrawn_transaction in parse_message_passed_event(transaction, self._l2_to_l1_message_passer)
            ]
        )

        for data in result:
            self._collect_item(data.type(), data)
