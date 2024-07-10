#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/10 11:29
# @Author  will
# @File  arb_parser.py
# @Brief
import json

from web3._utils.contracts import decode_transaction_data
from web3.types import ABIEvent, ABIFunction
from typing import Any, Dict, cast
from dataclasses import dataclass


from extractor.signature import event_log_abi_to_topic, decode_log, function_abi_to_4byte_selector_str

MESSAGE_DELIVERED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageIndex","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeInboxAcc","type":"bytes32"},{"indexed":false,"internalType":"address","name":"inbox","type":"address"},{"indexed":false,"internalType":"uint8","name":"kind","type":"uint8"},{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"bytes32","name":"messageDataHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"baseFeeL1","type":"uint256"},{"indexed":false,"internalType":"uint64","name":"timestamp","type":"uint64"}],"name":"MessageDelivered","type":"event"}"""))
MESSAGE_DELIVERED_EVENT_SIG = event_log_abi_to_topic(MESSAGE_DELIVERED_EVENT)

INBOX_MESSAGE_DELIVERED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageNum","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"InboxMessageDelivered","type":"event"}"""))
INBOX_MESSAGE_DELIVERED_EVENT_SIG = event_log_abi_to_topic(INBOX_MESSAGE_DELIVERED_EVENT)

BRIDGE_CALL_TRIGGERED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"outbox","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"BridgeCallTriggered","type":"event"}"""))
BRIGHT_CALL_TRIGGERED_EVENT_SIG = event_log_abi_to_topic(BRIDGE_CALL_TRIGGERED_EVENT)

WITHDRAWAL_INITIATED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"l1Token","type":"address"},{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_l2ToL1Id","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_exitNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"WithdrawalInitiated","type":"event"}"""))
WITHDRAWAL_INITIATED_EVENT_SIG = event_log_abi_to_topic(WITHDRAWAL_INITIATED_EVENT)

TICKET_CREATED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"ticketId","type":"bytes32"}],"name":"TicketCreated","type":"event"}"""))
TICKET_CREATED_EVENT_SIG = event_log_abi_to_topic(TICKET_CREATED_EVENT)

TxToL1_GW_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_id","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"_data","type":"bytes"}],"name":"TxToL1","type":"event"}"""))
TxToL1_GW_EVENT_SIG = event_log_abi_to_topic(TxToL1_GW_EVENT)

L2ToL1Tx_64_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"destination","type":"address"},{"indexed":true,"internalType":"uint256","name":"hash","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"position","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"arbBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"ethBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"timestamp","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"callvalue","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"L2ToL1Tx","type":"event"}"""))
L2ToL1Tx64_EVENT_SIG = event_log_abi_to_topic(L2ToL1Tx_64_EVENT)

SEQUENCER_BATCH_DELIVERED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"batchSequenceNumber","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeAcc","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"afterAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"delayedAcc","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"components":[{"internalType":"uint64","name":"minTimestamp","type":"uint64"},{"internalType":"uint64","name":"maxTimestamp","type":"uint64"},{"internalType":"uint64","name":"minBlockNumber","type":"uint64"},{"internalType":"uint64","name":"maxBlockNumber","type":"uint64"}],"indexed":false,"internalType":"struct IBridge.TimeBounds","name":"timeBounds","type":"tuple"},{"indexed":false,"internalType":"enum IBridge.BatchDataLocation","name":"dataLocation","type":"uint8"}],"name":"SequencerBatchDelivered","type":"event"}"""))
SEQUENCER_BATCH_DELIVERED_EVENT_SIG = event_log_abi_to_topic(SEQUENCER_BATCH_DELIVERED_EVENT)

NODE_CREATED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":true,"internalType":"bytes32","name":"parentNodeHash","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"nodeHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"executionHash","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"beforeState","type":"tuple"},{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"afterState","type":"tuple"},{"internalType":"uint64","name":"numBlocks","type":"uint64"}],"indexed":false,"internalType":"struct RollupLib.Assertion","name":"assertion","type":"tuple"},{"indexed":false,"internalType":"bytes32","name":"afterInboxBatchAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"wasmModuleRoot","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"inboxMaxCount","type":"uint256"}],"name":"NodeCreated","type":"event"}"""))
NODE_CREATED_EVENT_SIG = "0x4f4caa9e67fb994e349dd35d1ad0ce23053d4323f83ce11dc817b5435031d096"

NODE_CONFIRMED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":false,"internalType":"bytes32","name":"blockHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"sendRoot","type":"bytes32"}],"name":"NodeConfirmed","type":"event"}"""))
NODE_CONFIRMED_EVENT_SIG = "0x22ef0479a7ff660660d1c2fe35f1b632cf31675c2d9378db8cec95b00d8ffa3c"

BEACON_UPGRADED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"beacon","type":"address"}],"name":"BeaconUpgraded","type":"event"}"""))
BEACON_UPGRADED_EVENT_SIG = event_log_abi_to_topic(BEACON_UPGRADED_EVENT)

DEPOSIT_FINALIZED_EVENT = cast(ABIEvent, json.loads(
    """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"receiver","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"DepositFinalized","type":"event"}"""))
DEPOSIT_FINALIZED_EVENT_SIG = event_log_abi_to_topic(DEPOSIT_FINALIZED_EVENT)


EXECUTE_TRANSACTION_FUNCTION = cast(ABIFunction, json.loads(
    """{"inputs":[{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"address","name":"l2Sender","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"l2Block","type":"uint256"},{"internalType":"uint256","name":"l1Block","type":"uint256"},{"internalType":"uint256","name":"l2Timestamp","type":"uint256"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"executeTransaction","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))
EXECUTE_TRANSACTION_FUNCTION_SIG = function_abi_to_4byte_selector_str(EXECUTE_TRANSACTION_FUNCTION)

ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION = cast(ABIFunction, json.loads(
    """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromBlobs","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))
ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION_SIG = function_abi_to_4byte_selector_str(ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION)

ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION = cast(ABIFunction, json.loads(
    """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"name":"data","type":"bytes","internalType":"bytes"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromOrigin","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))
ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION_SIG = function_abi_to_4byte_selector_str(ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION)

OUT_BOUND_TRANSFER_FUNCTION = cast(ABIFunction, json.loads(
    """{"inputs":[{"name":"_l1Token","type":"address","internalType":"address"},{"name":"_to","type":"address","internalType":"address"},{"name":"_amount","type":"uint256","internalType":"uint256"},{"name":"a","type":"uint256","internalType":"uint256"},{"name":"b","type":"uint256","internalType":"uint256"},{"name":"_data","type":"bytes","internalType":"bytes"}],"name":"outboundTransfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}"""))
OUT_BOUND_TRANSFER_FUNCTION_SIG = function_abi_to_4byte_selector_str(OUT_BOUND_TRANSFER_FUNCTION)


class Constants:
    L2_MSG = 3
    L1MessageType_L2FundedByL1 = 7
    L1MessageType_submitRetryableTx = 9
    L1MessageType_ethDeposit = 12
    L1MessageType_batchPostingReport = 13
    L2MessageType_unsignedEOATx = 0
    L2MessageType_unsignedContractTx = 1

    ROLLUP_PROTOCOL_EVENT_TYPE = 8
    INITIALIZATION_MSG_TYPE = 11

    ZERO_ADDRESS = bytes(20)
    ZERO_ADDRESS_32 = bytes(32)


@dataclass
class MessageDeliveredData:
    msg_hash: str
    block_number: int
    block_timestamp: int
    block_hash: str
    transaction_hash: str
    from_address: str
    to_address: str
    bridge_from_address: str
    bridge_to_address: str
    extra_info: Dict[str, Any]
    beforeInboxAcc: str
    messageIndex: int
    inbox: str
    kind: int
    sender: str
    messageDataHash: str
    baseFeeL1: int
    timestamp: int


@dataclass
class InboxMessageDeliveredData:
    transaction_hash: str
    msg_number: int
    data: str


@dataclass
class TicketCreatedData:
    msg_hash: str
    transaction_hash: str
    block_number: int
    block_timestamp: int
    block_hash: str
    from_address: str
    to_address: str


@dataclass
class BridgeCallTriggeredData:
    msg_hash: str
    l1_transaction_hash: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_from_address: str
    l1_to_address: str
    outbox: str
    to: str
    value: int
    data: str


@dataclass
class L2ToL1Tx_64:
    msg_hash: str
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str
    l2_token_address: str
    caller: str
    destination: str
    hash: str
    position: int
    arbBlockNum: int
    ethBlockNum: int
    timestamp: int
    callvalue: int
    data: str


@dataclass
class TransactionToken:
    transaction_hash: str
    l1Token: str
    amount: int


@dataclass
class ArbitrumTransactionBatch:
    batch_index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    end_block_number: str
    start_block_number: str
    transaction_count: int


ZERO_ADDRESS_32 = bytes(32)
ZERO_ADDRESS = bytes(20)


def strip_leading_zeros(byte_array: bytes) -> bytes:
    if byte_array != ZERO_ADDRESS_32:
        return byte_array.lstrip(b'\x00')
    else:
        return ZERO_ADDRESS


def parse_message_delivered(transaction, contract_set):
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == MESSAGE_DELIVERED_EVENT_SIG and log.address in contract_set:
            event = decode_log(MESSAGE_DELIVERED_EVENT, log)

            messageIndex = event.get("messageIndex")
            beforeInboxAcc = event.get("beforeInboxAcc")
            inbox = event.get("inbox")
            kind = event.get("kind")
            sender = event.get("sender")
            messageDataHash = event.get("messageDataHash")
            baseFeeL1 = event.get("baseFeeL1")
            timestamp = event.get("timestamp")
            mdd = MessageDeliveredData(
                msg_hash=None,
                block_number=transaction.blockNumber,
                block_timestamp=transaction.blockTimestamp,
                block_hash=transaction.blockHash,
                transaction_hash=transaction.hash,
                from_address=transaction.fromAddress,
                to_address=transaction.toAddress,
                bridge_from_address=sender,
                bridge_to_address=sender,
                extra_info={
                    "fee": baseFeeL1,
                    "kind": kind
                },
                beforeInboxAcc=beforeInboxAcc,
                messageIndex=messageIndex,
                inbox=inbox,
                kind=kind,
                sender=sender,
                messageDataHash=messageDataHash,
                baseFeeL1=baseFeeL1,
                timestamp=timestamp,
            )
            res.append(mdd)
    return res


def parse_ticket_created_event(transaction, contract_set):
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == TICKET_CREATED_EVENT_SIG and log.address in contract_set:
            event = decode_log(TICKET_CREATED_EVENT, log)
            tcd = TicketCreatedData(
                msg_hash=event.get("ticketId"),
                transaction_hash=transaction.hash,
                block_number=transaction.blockNumber,
                block_timestamp=transaction.blockTimestamp,
                block_hash=transaction.blockHash,
                from_address=transaction.fromAddress,
                to_address=transaction.toAddress,
            )
            res.append(tcd)
    return res


def un_marshal_tx_to_l1(data):
    """
     * outboundCalldata = abi.encodeWithSelector(
     * ITokenGateway.finalizeInboundTransfer.selector,
     * _token,
     * _from,
     * _to,
     * _amount,
     * GatewayMessageHandler.encodeFromL2GatewayMsg(exitNum, _data)
     * );
    """
    offset = 0
    selector = b""
    _token = ZERO_ADDRESS
    _from = ZERO_ADDRESS
    _to = ZERO_ADDRESS
    _amount = 0
    restData = b""

    selector = data[offset: offset + 4]
    offset += 4
    _token = data[offset, offset + 32]
    offset += 32
    _from = data[offset, offset + 32]
    offset += 32
    _to = data[offset, offset + 32]
    offset += 32
    _amount = data[offset, offset + 32]
    offset += 32
    restData = data[offset, data.length]
    return selector, _token, _from, _to, _amount, restData

def parse_l2_to_l1_tx_64_event(transaction, contract_set):
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == L2ToL1Tx64_EVENT_SIG and log.address in contract_set:
            event = decode_log(L2ToL1Tx_64_EVENT, log)
            msgNumber = event.get("position")
            data = event.get("data")
            selector, _token, _from, _to, _amount, restData = un_marshal_tx_to_l1(data)

            amount = _amount
            if amount == 0:
                amount = event.get("callvalue")

            l2tol1 = L2ToL1Tx_64(
                msg_hash=msgNumber.toByteArray,
                l2_block_number=transaction.blockNumber,
                l2_block_timestamp=transaction.blockTimestamp,
                l2_block_hash=transaction.blockHash,
                l2_transaction_hash=transaction.hash,
                l2_from_address=transaction.fromAddress,
                l2_to_address=transaction.toAddress,
                l2_token_address=_token,
                caller=event.get("caller"),
                destination=event.get("destination"),
                hash=event.get("hash"),
                position=event.get("position"),
                arbBlockNum=event.get("arbBlockNum"),
                ethBlockNum=event.get("ethBlockNum"),
                timestamp=event.get("timestamp"),
                callvalue=amount,
                data=data
            )
            res.append(l2tol1)
    return res


def parse_sequencer_batch_delivered(transaction, contract_set) -> list:
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == SEQUENCER_BATCH_DELIVERED_EVENT_SIG and log.address in contract_set:
            input = transaction.input
            input_sig = input.slice(0, 10)
            sequenceNumber = 0
            prevMessageCount = 0
            newMessageCount = 0
            gasRefunder = ZERO_ADDRESS
            afterDelayedMessagesRead = 0
            if (input_sig == ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION_SIG):
                decoded_input = decode_transaction_data(ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION, input)
                sequenceNumber = decoded_input.get("sequenceNumber").getOrElse(None).toString.toLong
                prevMessageCount = decoded_input.get("prevMessageCount").getOrElse(None).toString.toLong
                newMessageCount = decoded_input.get("newMessageCount").getOrElse(None).toString.toLong
                gasRefunder = (decoded_input.get("gasRefunder").getOrElse("").toString)
                afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead").getOrElse(
                    None).toString.toLong

            elif (input_sig == ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION_SIG):
                decoded_input = decode_transaction_data(ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION, transaction.input)
                sequenceNumber = decoded_input.get("sequenceNumber").getOrElse(None).toString.toLong
                prevMessageCount = decoded_input.get("prevMessageCount").getOrElse(None).toString.toLong
                newMessageCount = decoded_input.get("newMessageCount").getOrElse(None).toString.toLong
                gasRefunder = (decoded_input.get("gasRefunder").getOrElse("").toString)
                afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead").getOrElse(
                    None).toString.toLong
                data = decoded_input.get("data")
            at = ArbitrumTransactionBatch(
                batch_index=sequenceNumber,
                l1_block_number=transaction.blockNumber,
                l1_block_timestamp=transaction.blockTimestamp,
                l1_block_hash=transaction.blockHash,
                l1_transaction_hash=transaction.hash,

                end_block_number=newMessageCount,
                start_block_number=prevMessageCount,
            )
            res.append(at)
    return res

def parseOutboundTransferFunction(self, transactions, contracts):
    res = []
    for tnx in transactions:
        if tnx.to in contracts:
            input_sig = tnx.input[0:10]
            if input_sig == ArbAbiClass.OutboundTransferFunction.signature:
                decoded_input = decode_transaction_data(ArbAbiClass.OutboundTransferFunction, tnx.input)
                tt = TransactionToken(
                    transaction_hash=tnx.hash,
                    l1Token=decoded_input["_l1Token"],
                    amount=decoded_input["_amount"],
                )
                res.append(tt)
    return res