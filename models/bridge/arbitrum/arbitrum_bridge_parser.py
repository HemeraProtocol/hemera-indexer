#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/9 10:05
# @Author  will
# @File  arb_bridge.py
# @Brief
import logging
from enum import Enum
from typing import List

from eth_utils import to_checksum_address

from models.bridge.arbitrum.arb_parser import *
from models.bridge.arbitrum.arb_rlp import calculate_submit_retryable_id, calculate_deposit_tx_id
from models.bridge.extractor import Extractor
from models.bridge.items import ARB_L1ToL2_ON_L1, ARB_L2ToL1_ON_L1, ARB_L2ToL1_ON_L2
from models.types import dict_to_dataclass, Transaction

logger = logging.getLogger(__name__)


class ArbType(Enum):

    BRIDGE_NATIVE = 1
    BRIDGE_ERC20 = 2
    BRIDGE_ERC721 = 3

    NORMAL_CROSS_CHAIN_CALL = 7

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


class ArbitrumL1BridgeDataExtractor(Extractor):

    def __init__(self, contract_list: list):
        super().__init__()
        self.contract_list = [x.lower() for x in contract_list]
        self.contract_set = set(self.contract_list)

    def get_filter(self):
        topics = []
        addresses = self.contract_list

        topics.append(MESSAGE_DELIVERED_EVENT_SIG)
        topics.append(INBOX_MESSAGE_DELIVERED_EVENT_SIG)
        topics.append(BRIDGE_CALL_TRIGGERED_EVENT_SIG)
        topics.append(NODE_CREATED_EVENT_SIG)
        topics.append(NODE_CONFIRMED_EVENT_SIG)

        filter_params = {
            "topics": [
                topics
            ],
            "address": [
                to_checksum_address(address) for address in addresses
            ],
        }
        return filter_params

    def extract_bridge_data(self, transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:

        result = []
        transactions = [(dict_to_dataclass(tx, Transaction)) for tx in transactions]
        tnx_input = parse_outbound_transfer_function(transactions, self.contract_set)
        tnx_input_map = {}
        for tnx in tnx_input:
            tnx_input_map[str(tnx.transaction_hash)] = tnx
        message_delivered_event_list = list(map(lambda x: parse_message_delivered(x, self.contract_set), transactions))
        message_delivered_event_map = {m.messageIndex: m for sublist in message_delivered_event_list for m in sublist}
        inbox_message_delivered_event_list = list(map(lambda x: parse_inbox_message_delivered(x, self.contract_set), transactions))
        inbox_message_delivered_event_map = {m.msg_number: m for sublist in inbox_message_delivered_event_list for m in sublist}
        # merge two objects by msgNumber, l1 -> l2
        arb_deposit_lis = []
        for msg_num, inbox_message in inbox_message_delivered_event_map.items():
            token_transaction = tnx_input_map.get(inbox_message.transaction_hash)
            message_deliver = message_delivered_event_map.get(msg_num)
            if not message_deliver:
                continue
            kind = message_deliver.kind if message_deliver.kind else -1
            (destAddress, l2CallValue, msgValue, gasLimit, maxSubmissionCost, excessFeeRefundAddress,
             callValueRefundAddress,
             maxFeePerGas, dataHex, l1TokenId, l1TokenAmount) = un_marshal_inbox_message_delivered_data(kind,
                                                                                                          inbox_message.data)
            l2_chain_id = env["l2_chain_id"]
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
                    dataHex
                )
                if token_transaction:
                    if token_transaction.l1Token:
                        l1TokenId = token_transaction.l1Token
                    if token_transaction.amount:
                        l1TokenAmount = token_transaction.amount

                qdt = {
                    "item": ARB_L1ToL2_ON_L1,
                    'msg_hash': l2_tx_hash,
                    'index': message_deliver.messageIndex,
                    'l1_block_number': message_deliver.block_number,
                    'l1_block_timestamp': message_deliver.block_timestamp,
                    'l1_block_hash': message_deliver.block_hash,
                    'l1_transaction_hash': message_deliver.transaction_hash,
                    'l1_from_address': message_deliver.from_address,
                    'l1_to_address': message_deliver.to_address,
                    'l1_token_address': l1TokenId,
                    'l2_token_address': None,
                    'from_address': message_deliver.bridge_from_address,
                    'to_address': message_deliver.bridge_to_address,
                    'amount': l1TokenAmount,
                    'extra_info': message_deliver.extra_info,
                    '_type': ArbType.BRIDGE_NATIVE.value,
                }
                arb_deposit_lis.append(qdt)
            elif kind == 12:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue
                )
                qdt = {
                    "item": ARB_L1ToL2_ON_L1,
                    'msg_hash': l2_tx_hash,
                    'index': msg_num,
                    'l1_block_number': message_deliver.block_number,
                    'l1_block_timestamp': message_deliver.block_timestamp,
                    'l1_block_hash': message_deliver.block_hash,
                    'l1_transaction_hash': message_deliver.transaction_hash,
                    'l1_from_address': message_deliver.from_address,
                    'l1_to_address': message_deliver.to_address,
                    'l1_token_address': strip_leading_zeros(l1TokenId),
                    'l2_token_address': None,
                    'from_address': message_deliver.bridge_from_address,
                    'to_address': message_deliver.bridge_to_address,
                    'amount': l1TokenAmount,
                    'extra_info': message_deliver.extra_info,
                    '_type': 1
                }
                arb_deposit_lis.append(qdt)
            elif kind == 11:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue
                )
                qdt = {
                    "item": ARB_L1ToL2_ON_L1,
                    'msg_hash': l2_tx_hash,
                    'index': msg_num,
                    'l1_block_number': message_deliver.block_number,
                    'l1_block_timestamp': message_deliver.block_timestamp,
                    'l1_block_hash': message_deliver.block_hash,
                    'l1_transaction_hash': message_deliver.transaction_hash,
                    'l1_from_address': message_deliver.from_address,
                    'l1_to_address': message_deliver.to_address,
                    'l1_token_address': strip_leading_zeros(l1TokenId) if l1TokenId else None,
                    'l2_token_address': None,
                    'from_address': message_deliver.bridge_from_address,
                    'to_address': message_deliver.bridge_to_address,
                    'amount': l1TokenAmount,
                    'extra_info': message_deliver.extra_info,
                    '_type': 1
                }
                arb_deposit_lis.append(qdt)
            elif kind == 3:
                l2_tx_hash = calculate_deposit_tx_id(
                    l2_chain_id,
                    msg_num,
                    message_deliver.sender,
                    message_deliver.from_address,
                    msgValue
                )
                qdt = {
                    "item": ARB_L1ToL2_ON_L1,
                    'msg_hash': l2_tx_hash,
                    'index': msg_num,
                    'l1_block_number': message_deliver.block_number,
                    'l1_block_timestamp': message_deliver.block_timestamp,
                    'l1_block_hash': message_deliver.block_hash,
                    'l1_transaction_hash': message_deliver.transaction_hash,
                    'l1_from_address': message_deliver.from_address,
                    'l1_to_address': message_deliver.to_address,
                    'l1_token_address': strip_leading_zeros(l1TokenId) if l1TokenId else None,
                    'l2_token_address': None,
                    'from_address': message_deliver.bridge_from_address,
                    'to_address': message_deliver.bridge_to_address,
                    'amount': l1TokenAmount,
                    'extra_info': message_deliver.extra_info,
                    '_type': 1
                }
                arb_deposit_lis.append(qdt)
        result += arb_deposit_lis
        # l2 -> l1
        bridge_call_triggered_transaction = []
        for tnx in transactions:
            x = parse_bridge_call_triggered(tnx, self.contract_set)
            for z in x:
                dic = {
                    "item": ARB_L2ToL1_ON_L1,
                    'msg_hash': z.msg_hash,
                    'l1_transaction_hash': z.l1_transaction_hash,
                    'l1_block_number': z.l1_block_number,
                    'l1_block_timestamp': z.l1_block_timestamp,
                    'l1_block_hash': z.l1_block_hash,
                    'l1_from_address': z.l1_from_address,
                    'l1_to_address': z.l1_to_address,
                    'outbox': z.outbox,
                    'to': z.to,
                    'value': z.value,
                    'data': z.data
                }
                bridge_call_triggered_transaction.append(dic)
        result += bridge_call_triggered_transaction

        tnx_batches = [item for x in transactions for item in parse_sequencer_batch_delivered(x, self.contract_set)]
        state_create_batches = [item for x in transactions for item in parse_node_created(x, self.contract_set)]
        state_confirm_batches = [item for x in transactions for item in parse_node_confirmed(x, self.contract_set)]

        result += tnx_batches
        result += state_create_batches
        result += state_confirm_batches
        return result


class ArbitrumL2BridgeDataExtractor(Extractor):

    def __init__(self, contract_list: list):
        super().__init__()
        self.contract_list = [x.lower() for x in contract_list]
        self.contract_set = set(self.contract_list)

    def get_filter(self):
        topics = []
        addresses = self.contract_list

        topics.append(TICKET_CREATED_EVENT_SIG)
        topics.append(L2ToL1Tx64_EVENT_SIG)
        topics.append(BEACON_UPGRADED_EVENT_SIG)
        topics.append(DEPOSIT_FINALIZED_EVENT_SIG)

        filter_params = {
            "topics": [
                topics
            ],
            "address": [
                to_checksum_address(address) for address in addresses
            ],
        }
        return filter_params

    def extract_bridge_data(self, transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        transactions = [(dict_to_dataclass(tx, Transaction)) for tx in transactions]

        result = []
        # l1 -> l2
        ticket_created = []
        for tnx in transactions:
            x_lis = parse_ticket_created_event(tnx, self.contract_set)
            for x in x_lis:
                adt = {
                    'item': ARB_L2ToL1_ON_L2,
                    'msg_hash': x.msg_hash,
                    'l2_block_number': x.block_number,
                    'l2_block_timestamp': x.block_timestamp,
                    'l2_block_hash': x.block_hash,
                    'l2_transaction_hash': x.transaction_hash,
                    'l2_from_address': x.from_address,
                    'l2_to_address': x.to_address,
                }
                ticket_created.append(adt)
        # l2 -> l1
        l2_to_l1 = []
        for tnx in transactions:
            x_lis = parse_l2_to_l1_tx_64_event(tnx, self.contract_set)
            for x in x_lis:
                arb = {
                    'item': ARB_L2ToL1_ON_L2,
                    'msg_hash': x.msg_hash,
                    'index': x.position,
                    'l2_block_number': x.l2_block_number,
                    'l2_block_timestamp': x.l2_block_timestamp,
                    'l2_block_hash': x.l2_block_hash,
                    'l2_transaction_hash': x.l2_transaction_hash,
                    'l2_from_address': x.l2_from_address,
                    'l2_to_address': x.l2_to_address,
                    'amount': x.callvalue,
                    'from_address': x.caller,
                    'to_address': x.destination,
                    'l1_token_address': None,
                    'l2_token_address': strip_leading_zeros(x.l2_token_address),
                    'extra_info': None,
                }
                l2_to_l1.append(arb)
        bridge_tokens = []
        for tnx in transactions:
            x = parse_bridge_token(tnx, self.contract_set)
            bridge_tokens.extend(x)
        result += ticket_created
        result += l2_to_l1
        result += bridge_tokens
        return result