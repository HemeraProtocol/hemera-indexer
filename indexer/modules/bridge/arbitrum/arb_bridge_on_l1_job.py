import logging

from indexer.domains.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.bridge.arbitrum.arb_parser import *
from indexer.modules.bridge.arbitrum.arb_rlp import calculate_deposit_tx_id, calculate_submit_retryable_id
from indexer.modules.bridge.domain.arbitrum import ArbitrumL1ToL2TransactionOnL1, ArbitrumL2ToL1TransactionOnL1
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ArbitrumBridgeOnL1Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [
        ArbitrumL1ToL2TransactionOnL1,
        ArbitrumL2ToL1TransactionOnL1,
        ArbitrumStateBatchConfirmed,
        ArbitrumStateBatchCreated,
        ArbitrumTransactionBatch,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"]

        self._contract_list = [address.lower() for address in set(config.get("contract_list"))]
        self.l2_chain_id = int(config.get("l2_chain_id"))
        self.transaction_batch_offset = int(config.get("transaction_batch_offset"))

    def get_filter(self):
        topics = []
        addresses = self._contract_list

        topics.append(MESSAGE_DELIVERED_EVENT_SIG)
        topics.append(INBOX_MESSAGE_DELIVERED_EVENT_SIG)
        topics.append(BRIDGE_CALL_TRIGGERED_EVENT_SIG)
        topics.append(NODE_CREATED_EVENT_SIG)
        topics.append(NODE_CONFIRMED_EVENT_SIG)
        topics.append(SEQUENCER_BATCH_DELIVERED_EVENT_SIG)

        return TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)])

    def _process(self, **kwargs):
        # filter out transactions that are not bridge related
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []

        tnx_input = parse_outbound_transfer_function(transactions, self._contract_list)
        tnx_input_map = {}
        for tnx in tnx_input:
            tnx_input_map[str(tnx.transaction_hash)] = tnx
        message_delivered_event_list = list(
            map(lambda x: parse_message_delivered(x, self._contract_list), transactions)
        )
        message_delivered_event_map = {m.messageIndex: m for sublist in message_delivered_event_list for m in sublist}
        inbox_message_delivered_event_list = list(
            map(
                lambda x: parse_inbox_message_delivered(x, self._contract_list),
                transactions,
            )
        )
        inbox_message_delivered_event_map = {
            m.msg_number: m for sublist in inbox_message_delivered_event_list for m in sublist
        }
        # merge two objects by msgNumber, l1 -> l2
        arb_deposit_lis = []
        for msg_num, inbox_message in inbox_message_delivered_event_map.items():
            token_transaction = tnx_input_map.get(inbox_message.transaction_hash)
            message_deliver = message_delivered_event_map.get(msg_num)
            if not message_deliver:
                continue
            kind = message_deliver.kind if message_deliver.kind else -1
            l2_chain_id = self.l2_chain_id
            (
                destAddress,
                l2CallValue,
                msgValue,
                gasLimit,
                maxSubmissionCost,
                excessFeeRefundAddress,
                callValueRefundAddress,
                maxFeePerGas,
                dataHex,
                l1TokenId,
                l1TokenAmount,
            ) = un_marshal_inbox_message_delivered_data(kind, inbox_message.data, l2_chain_id)

            if kind == 9:
                l2_tx_hash = calculate_submit_retryable_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.baseFeeL1,
                    strip_leading_zeros(destAddress),
                    l2CallValue,
                    msgValue,
                    maxSubmissionCost,
                    strip_leading_zeros(excessFeeRefundAddress),
                    strip_leading_zeros(callValueRefundAddress),
                    gasLimit,
                    maxFeePerGas,
                    dataHex,
                )
                if token_transaction:
                    if token_transaction.l1Token:
                        l1TokenId = token_transaction.l1Token
                    if token_transaction.amount:
                        l1TokenAmount = token_transaction.amount

                qdt = ArbitrumL1ToL2TransactionOnL1(
                    msg_hash=l2_tx_hash,
                    index=msg_num,
                    l1_block_number=message_deliver.block_number,
                    l1_block_timestamp=message_deliver.block_timestamp,
                    l1_block_hash=message_deliver.block_hash,
                    l1_transaction_hash=message_deliver.transaction_hash,
                    l1_from_address=message_deliver.from_address,
                    l1_to_address=message_deliver.to_address,
                    l1_token_address=l1TokenId,
                    l2_token_address=None,
                    from_address=message_deliver.bridge_from_address,
                    to_address=message_deliver.bridge_to_address,
                    amount=l1TokenAmount,
                    extra_info=message_deliver.extra_info,
                    _type=ArbType.BRIDGE_NATIVE.value,
                )
                arb_deposit_lis.append(qdt)
            elif kind == 12:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue,
                )
                qdt = ArbitrumL1ToL2TransactionOnL1(
                    msg_hash=l2_tx_hash,
                    index=msg_num,
                    l1_block_number=message_deliver.block_number,
                    l1_block_timestamp=message_deliver.block_timestamp,
                    l1_block_hash=message_deliver.block_hash,
                    l1_transaction_hash=message_deliver.transaction_hash,
                    l1_from_address=message_deliver.from_address,
                    l1_to_address=message_deliver.to_address,
                    l1_token_address=(strip_leading_zeros(l1TokenId) if l1TokenId else None),
                    l2_token_address=None,
                    from_address=message_deliver.bridge_from_address,
                    to_address=message_deliver.bridge_to_address,
                    amount=l1TokenAmount,
                    extra_info=message_deliver.extra_info,
                    _type=1,
                )

                arb_deposit_lis.append(qdt)
            elif kind == 11:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue,
                )
                qdt = ArbitrumL1ToL2TransactionOnL1(
                    msg_hash=l2_tx_hash,
                    index=msg_num,
                    l1_block_number=message_deliver.block_number,
                    l1_block_timestamp=message_deliver.block_timestamp,
                    l1_block_hash=message_deliver.block_hash,
                    l1_transaction_hash=message_deliver.transaction_hash,
                    l1_from_address=message_deliver.from_address,
                    l1_to_address=message_deliver.to_address,
                    l1_token_address=(strip_leading_zeros(l1TokenId) if l1TokenId else None),
                    l2_token_address=None,
                    from_address=message_deliver.bridge_from_address,
                    to_address=message_deliver.bridge_to_address,
                    amount=l1TokenAmount,
                    extra_info=message_deliver.extra_info,
                    _type=1,
                )
                arb_deposit_lis.append(qdt)
            elif kind == 3:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue,
                )
                arb_deposit_lis.append(
                    ArbitrumL1ToL2TransactionOnL1(
                        msg_hash=l2_tx_hash,
                        index=msg_num,
                        l1_block_number=message_deliver.block_number,
                        l1_block_timestamp=message_deliver.block_timestamp,
                        l1_block_hash=message_deliver.block_hash,
                        l1_transaction_hash=message_deliver.transaction_hash,
                        l1_from_address=message_deliver.from_address,
                        l1_to_address=message_deliver.to_address,
                        l1_token_address=(strip_leading_zeros(l1TokenId) if l1TokenId else None),
                        l2_token_address=None,
                        from_address=message_deliver.bridge_from_address,
                        to_address=message_deliver.bridge_to_address,
                        amount=l1TokenAmount,
                        extra_info=message_deliver.extra_info,
                        _type=1,
                    )
                )
        result += arb_deposit_lis
        # l2 -> l1
        bridge_call_triggered_transaction = []
        for tnx in transactions:
            x = parse_bridge_call_triggered(tnx, self._contract_list)
            for z in x:
                bridge_call_triggered_transaction.append(
                    ArbitrumL2ToL1TransactionOnL1(
                        msg_hash=z.msg_hash,
                        l1_transaction_hash=z.l1_transaction_hash,
                        l1_block_number=z.l1_block_number,
                        l1_block_timestamp=z.l1_block_timestamp,
                        l1_block_hash=z.l1_block_hash,
                        l1_from_address=z.l1_from_address,
                        l1_to_address=z.l1_to_address,
                    )
                )
        result += bridge_call_triggered_transaction

        tnx_batches = [
            item
            for x in transactions
            for item in parse_sequencer_batch_delivered(x, self._contract_list, self.transaction_batch_offset)
        ]
        state_create_batches = [item for x in transactions for item in parse_node_created(x, self._contract_list)]
        state_confirm_batches = [item for x in transactions for item in parse_node_confirmed(x, self._contract_list)]

        result += tnx_batches
        result += state_create_batches
        result += state_confirm_batches
        for data in result:
            self._collect_item(data.type(), data)
