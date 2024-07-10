#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/9 10:05
# @Author  will
# @File  arb_bridge.py
# @Brief
import logging

from extractor.bridge.arbitrum.arb_rlp import calculate_submit_retryable_id, calculate_deposit_tx_id

from arb_parser import *

env = {}
logger = logging.getLogger(__name__)


@dataclass
class ArbDepositTransactionOnL1WithHash:
    msg_hash: str
    index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    l1_from_address: str
    l1_to_address: str
    amount: int
    from_address: str
    to_address: str
    l1_token_address: str
    l2_token_address: str
    extra_info: dict
    _type: int


@dataclass
class ArbDepositTransactionOnL2:
    msg_hash: str
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str


@dataclass
class ArbWithdrawalTransactionOnL2:
    msg_hash: str
    version: int
    index: int
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str
    amount: int
    from_address: str
    to_address: str
    l1_token_address: str
    l2_token_address: str
    extra_info: dict
    _type: int


class ArbitrumBridgeExtractor:

    def __init__(self):
        pass

    def l1_contract_extractor(self, transactions, contract_list) -> list:
        contract_set = set(contract_list)
        res = []
        tnx_input = parse_outbound_transfer_function(transactions, contract_set)
        tnx_input_map = {}
        for tnx in tnx_input:
            tnx_input_map[tnx['hash']] = tnx
        message_delivered_event_list = map(lambda x: parse_message_delivered(x, contract_set), transactions)
        message_delivered_event_map = {m.messageIndex: m for m in message_delivered_event_list}
        inbox_message_delivered_event_list = map(lambda x: parse_inbox_message_delivered(x, contract_set), transactions)
        inbox_message_delivered_event_map = {m.msg_number: m for m in inbox_message_delivered_event_list}
        # merge two objects by msgNumber, l1 -> l2
        for msg_num, inbox_message in inbox_message_delivered_event_map.items():
            token_transaction = tnx_input_map.get(inbox_message.transaction_hash)
            message_deliver = message_delivered_event_map.get(msg_num)
            kind = message_deliver.kind if message_deliver.kind else -1
            (destAddress, l2CallValue, msgValue, gasLimit, maxSubmissionCost, excessFeeRefundAddress,
             callValueRefundAddress,
             maxFeePerGas, dataBytes, l1TokenId, l1TokenAmount) = un_marshal_inbox_message_delivered_data(kind,
                                                                                                          inbox_message.data)
            l2_chain_id = env["l2_chain_id"]
            if kind == 9:
                l2_tx_hash = calculate_submit_retryable_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.baseFeeL1,
                    destAddress,
                    l2CallValue,
                    msgValue,
                    maxSubmissionCost,
                    excessFeeRefundAddress,
                    callValueRefundAddress,
                    gasLimit,
                    maxFeePerGas,
                    dataBytes
                )
                if token_transaction:
                    if token_transaction.l1Token:
                        l1TokenId = token_transaction.l1Token
                    if token_transaction.amount:
                        msgValue = token_transaction.amount

                qdt = ArbDepositTransactionOnL1WithHash(
                    msg_hash=l2_tx_hash,
                    index=x.msg_number,
                    l1_block_number=message_deliver.block_number,
                    l1_block_timestamp=message_deliver.block_timestamp,
                    l1_block_hash=message_deliver.block_hash,
                    l1_transaction_hash=message_deliver.transaction_hash,
                    l1_from_address=message_deliver.from_address,
                    l1_to_address=message_deliver.to_address,
                    l1_token_address=(l1TokenId),
                    l2_token_address=None,
                    from_address=message_deliver.bridge_from_address,
                    to_address=message_deliver.bridge_to_address,
                    amount=msgValue,
                    extra_info=message_deliver.extra_info,
                    _type=1
                )
            elif kind == 12:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue
                )
                qdt = ArbDepositTransactionOnL1WithHash(
                    msg_hash=l2_tx_hash,
                    index=msg_num,
                    l1_block_number=message_deliver.block_number,
                    l1_block_timestamp=message_deliver.block_timestamp,
                    l1_block_hash=message_deliver.block_hash,
                    l1_transaction_hash=message_deliver.transaction_hash,
                    l1_from_address=message_deliver.from_address,
                    l1_to_address=message_deliver.to_address,
                    l1_token_address=(l1TokenId),
                    l2_token_address=None,
                    from_address=message_deliver.bridge_from_address,
                    to_address=message_deliver.bridge_to_address,
                    amount=msgValue,
                    extra_info=message_deliver.extra_info,
                    _type=1
                )
                pass

        # l2 -> l1
        bridge_call_triggered_transaction = []
        for tnx in transactions:
            awt = parse_bridge_call_triggered(tnx, contract_set)

        # TODO update to database

    def l2_contract_extractor(self, transactions, contract_list):
        contract_set = set(contract_list)
        # l1 -> l2
        ticket_created = []
        for tnx in transactions:
            x = parse_ticket_created_event(tnx, contract_set)
            adt = ArbDepositTransactionOnL2(
                msg_hash=x.msg_hash,
                l2_block_number=x.block_number,
                l2_block_timestamp=x.block_timestamp,
                l2_block_hash=x.block_hash,
                l2_transaction_hash=x.transaction_hash,
                l2_from_address=x.from_address,
                l2_to_address=x.to_address,
            )
            ticket_created.append(adt)
        # l2 -> l1
        l2_to_l1 = []
        for tnx in transactions:
            x = parse_l2_to_l1_tx_64_event(tnx, contract_set)
            arb = ArbWithdrawalTransactionOnL2(
                msg_hash=x.msg_hash,
                version=None,
                index=x.position,
                l2_block_number=x.l2_block_number,
                l2_block_timestamp=x.l2_block_timestamp,
                l2_block_hash=x.l2_block_hash,
                l2_transaction_hash=x.l2_transaction_hash,
                l2_from_address=x.l2_from_address,
                l2_to_address=x.l2_to_address,
                amount=x.callvalue,
                from_address=x.caller,
                to_address=x.destination,
                l1_token_address=None,
                l2_token_address=x.l2_token_address,
                extra_info=None,
                _type=None
            )
            l2_to_l1.append(arb)
        bridge_tokens = []
        for tnx in transactions:
            x = parse_bridge_token(tnx, contract_set)
            bridge_tokens.append(x)

        # TODO update to database

    def batch_extractor(self, transactions, contract_list):
        contract_set = set(contract_list)
        tnx_batches = map(lambda x: parse_sequencer_batch_delivered(x, contract_set), transactions)
        state_create_batches = map(lambda x: parse_node_created(x, contract_set), tnx_batches)
        state_confirm_batches = map(lambda x: parse_node_confirmed(x, contract_set), tnx_batches)
        # TODO update to database


if __name__ == "__main__":
    pass
