import logging

from indexer.domains.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.bridge.bedrock.parser.bedrock_bridge_parser import (
    BEDROCK_EVENT_ABI_SIGNATURE_MAPPING,
    parse_propose_l2_output,
    parse_relayed_message,
    parse_transaction_deposited_event,
)
from indexer.modules.bridge.domain.op_bedrock import *
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class BedrockBridgeOnL1Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [
        OpL1ToL2DepositedTransaction,
        OpL2ToL1WithdrawnTransactionProven,
        OpL2ToL1WithdrawnTransactionFinalized,
        OpStateBatch,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"]

        self._optimism_portal_proxy = config.get("optimism_portal_proxy")
        self._l2_output_oracle_proxy = config.get("l2_output_oracle_proxy")

        if self._optimism_portal_proxy:
            logger.info(f"OptimismPortalProxy: {self._optimism_portal_proxy}")
            self.optimism_portal_proxy = self._optimism_portal_proxy.lower()
        else:
            logger.warning("OptimismPortalProxy is None")
        if self._l2_output_oracle_proxy:
            logger.info(f"L2OutputOracleProxy: {self._optimism_portal_proxy}")
            self.l2_output_oracle_proxy = self._l2_output_oracle_proxy.lower()
        else:
            logger.warning("L2OutputOracleProxy is None")

    def get_filter(self):
        topic_filter_list = []
        if self._optimism_portal_proxy:
            topic_filter_list.append(
                TopicSpecification(
                    addresses=[self._optimism_portal_proxy],
                    topics=[
                        BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["TRANSACTION_DEPOSITED_EVENT"],
                        BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["WITHDRAWAL_FINALIZED_EVENT"],
                        BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["WITHDRAWAL_PROVEN_EVENT"],
                    ],
                )
            )
        if self._l2_output_oracle_proxy:
            topic_filter_list.append(
                TopicSpecification(
                    addresses=[self._l2_output_oracle_proxy],
                    topics=[BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["OUTPUT_PROPOSED_EVENT"]],
                )
            )
        return TransactionFilterByLogs(topic_filter_list)

    def _process(self, **kwargs):
        # filter out transactions that are not bridge related
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []
        if self._optimism_portal_proxy:
            l1_to_l2_deposit_transactions = [
                OpL1ToL2DepositedTransaction(
                    msg_hash=deposited_transaction.msg_hash,
                    version=deposited_transaction.version,
                    index=deposited_transaction.index,
                    l1_block_number=deposited_transaction.block_number,
                    l1_block_timestamp=deposited_transaction.block_timestamp,
                    l1_block_hash=deposited_transaction.block_hash,
                    l1_transaction_hash=deposited_transaction.transaction_hash,
                    l1_from_address=deposited_transaction.from_address,
                    l1_to_address=deposited_transaction.to_address,
                    amount=deposited_transaction.amount,
                    from_address=deposited_transaction.bridge_from_address,
                    to_address=deposited_transaction.bridge_to_address,
                    l1_token_address=deposited_transaction.remote_token_address,
                    l2_token_address=deposited_transaction.local_token_address,
                    extra_info=deposited_transaction.extra_info,
                    _type=deposited_transaction.bridge_transaction_type,
                    sender=deposited_transaction.sender,
                    target=deposited_transaction.target,
                    data=deposited_transaction.message,
                )
                for transaction in transactions
                for deposited_transaction in parse_transaction_deposited_event(transaction, self._optimism_portal_proxy)
            ]

            l2_to_l1_withdraw_transactions = [
                OpL2ToL1WithdrawnTransactionProven(
                    msg_hash=proven_transaction.msg_hash,
                    l1_proven_block_number=proven_transaction.block_number,
                    l1_proven_block_timestamp=proven_transaction.block_timestamp,
                    l1_proven_block_hash=proven_transaction.block_hash,
                    l1_proven_transaction_hash=proven_transaction.transaction_hash,
                    l1_proven_from_address=proven_transaction.from_address,
                    l1_proven_to_address=proven_transaction.to_address,
                )
                for transaction in transactions
                for proven_transaction in parse_relayed_message(
                    "WITHDRAWAL_PROVEN_EVENT",
                    transaction,
                    self._optimism_portal_proxy,
                    "withdrawalHash",
                )
            ]

            l2_to_l1_withdraw_transactions += [
                OpL2ToL1WithdrawnTransactionFinalized(
                    msg_hash=finalized_transaction.msg_hash,
                    l1_block_number=finalized_transaction.block_number,
                    l1_block_timestamp=finalized_transaction.block_timestamp,
                    l1_block_hash=finalized_transaction.block_hash,
                    l1_transaction_hash=finalized_transaction.transaction_hash,
                    l1_from_address=finalized_transaction.from_address,
                    l1_to_address=finalized_transaction.to_address,
                )
                for transaction in transactions
                for finalized_transaction in parse_relayed_message(
                    "WITHDRAWAL_FINALIZED_EVENT",
                    transaction,
                    self._optimism_portal_proxy,
                    "withdrawalHash",
                )
            ]

            result += l1_to_l2_deposit_transactions + l2_to_l1_withdraw_transactions

        if self._l2_output_oracle_proxy:
            op_state_batches = [
                OpStateBatch(
                    batch_index=op_state_batch.batch_index,
                    l1_block_number=op_state_batch.l1_block_number,
                    l1_block_timestamp=op_state_batch.l1_block_timestamp,
                    l1_block_hash=op_state_batch.l1_block_hash,
                    l1_transaction_hash=op_state_batch.l1_transaction_hash,
                    batch_root=op_state_batch.batch_root,
                    end_block_number=op_state_batch.end_block_number,
                )
                for transaction in transactions
                for op_state_batch in parse_propose_l2_output(transaction, self._l2_output_oracle_proxy)
            ]
            result += op_state_batches

        for data in result:
            self._collect_item(data.type(), data)
