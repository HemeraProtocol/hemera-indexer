#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/10 11:29
# @Author  will
# @File  arb_parser.py
# @Brief
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, cast

from eth_typing import ABIEvent, ABIFunction
from web3 import Web3
from web3._utils.contracts import decode_transaction_data

from hemera.common.utils.abi_code_utils import decode_log
from hemera.indexer.utils.abi import event_log_abi_to_topic, function_abi_to_4byte_selector_str
from hemera_udf.bridge.arbitrum.arb_network import Network
from hemera_udf.bridge.domains.arbitrum import (
    ArbitrumStateBatchConfirmed,
    ArbitrumStateBatchCreated,
    ArbitrumTransactionBatch,
    BridgeCallTriggeredData,
    BridgeToken,
    TicketCreatedData,
    TransactionToken,
)

MESSAGE_DELIVERED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageIndex","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeInboxAcc","type":"bytes32"},{"indexed":false,"internalType":"address","name":"inbox","type":"address"},{"indexed":false,"internalType":"uint8","name":"kind","type":"uint8"},{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"bytes32","name":"messageDataHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"baseFeeL1","type":"uint256"},{"indexed":false,"internalType":"uint64","name":"timestamp","type":"uint64"}],"name":"MessageDelivered","type":"event"}"""
    ),
)
MESSAGE_DELIVERED_EVENT_SIG = event_log_abi_to_topic(MESSAGE_DELIVERED_EVENT)

INBOX_MESSAGE_DELIVERED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageNum","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"InboxMessageDelivered","type":"event"}"""
    ),
)
INBOX_MESSAGE_DELIVERED_EVENT_SIG = event_log_abi_to_topic(INBOX_MESSAGE_DELIVERED_EVENT)

BRIDGE_CALL_TRIGGERED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"outbox","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"BridgeCallTriggered","type":"event"}"""
    ),
)
BRIDGE_CALL_TRIGGERED_EVENT_SIG = event_log_abi_to_topic(BRIDGE_CALL_TRIGGERED_EVENT)

WITHDRAWAL_INITIATED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"l1Token","type":"address"},{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_l2ToL1Id","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_exitNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"WithdrawalInitiated","type":"event"}"""
    ),
)
WITHDRAWAL_INITIATED_EVENT_SIG = event_log_abi_to_topic(WITHDRAWAL_INITIATED_EVENT)

TICKET_CREATED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"ticketId","type":"bytes32"}],"name":"TicketCreated","type":"event"}"""
    ),
)
TICKET_CREATED_EVENT_SIG = event_log_abi_to_topic(TICKET_CREATED_EVENT)

TxToL1_GW_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_id","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"_data","type":"bytes"}],"name":"TxToL1","type":"event"}"""
    ),
)
TxToL1_GW_EVENT_SIG = event_log_abi_to_topic(TxToL1_GW_EVENT)

L2ToL1Tx_64_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"destination","type":"address"},{"indexed":true,"internalType":"uint256","name":"hash","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"position","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"arbBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"ethBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"timestamp","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"callvalue","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"L2ToL1Tx","type":"event"}"""
    ),
)
L2ToL1Tx64_EVENT_SIG = event_log_abi_to_topic(L2ToL1Tx_64_EVENT)

SEQUENCER_BATCH_DELIVERED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"batchSequenceNumber","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeAcc","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"afterAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"delayedAcc","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"components":[{"internalType":"uint64","name":"minTimestamp","type":"uint64"},{"internalType":"uint64","name":"maxTimestamp","type":"uint64"},{"internalType":"uint64","name":"minBlockNumber","type":"uint64"},{"internalType":"uint64","name":"maxBlockNumber","type":"uint64"}],"indexed":false,"internalType":"struct IBridge.TimeBounds","name":"timeBounds","type":"tuple"},{"indexed":false,"internalType":"enum IBridge.BatchDataLocation","name":"dataLocation","type":"uint8"}],"name":"SequencerBatchDelivered","type":"event"}"""
    ),
)
SEQUENCER_BATCH_DELIVERED_EVENT_SIG = event_log_abi_to_topic(SEQUENCER_BATCH_DELIVERED_EVENT)

NODE_CREATED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":true,"internalType":"bytes32","name":"parentNodeHash","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"nodeHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"executionHash","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"beforeState","type":"tuple"},{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"afterState","type":"tuple"},{"internalType":"uint64","name":"numBlocks","type":"uint64"}],"indexed":false,"internalType":"struct RollupLib.Assertion","name":"assertion","type":"tuple"},{"indexed":false,"internalType":"bytes32","name":"afterInboxBatchAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"wasmModuleRoot","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"inboxMaxCount","type":"uint256"}],"name":"NodeCreated","type":"event"}"""
    ),
)
NODE_CREATED_EVENT_SIG = "0x4f4caa9e67fb994e349dd35d1ad0ce23053d4323f83ce11dc817b5435031d096"

NODE_CONFIRMED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":false,"internalType":"bytes32","name":"blockHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"sendRoot","type":"bytes32"}],"name":"NodeConfirmed","type":"event"}"""
    ),
)
NODE_CONFIRMED_EVENT_SIG = "0x22ef0479a7ff660660d1c2fe35f1b632cf31675c2d9378db8cec95b00d8ffa3c"

BEACON_UPGRADED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"beacon","type":"address"}],"name":"BeaconUpgraded","type":"event"}"""
    ),
)
BEACON_UPGRADED_EVENT_SIG = event_log_abi_to_topic(BEACON_UPGRADED_EVENT)

DEPOSIT_FINALIZED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"receiver","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"DepositFinalized","type":"event"}"""
    ),
)
DEPOSIT_FINALIZED_EVENT_SIG = event_log_abi_to_topic(DEPOSIT_FINALIZED_EVENT)

EXECUTE_TRANSACTION_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"address","name":"l2Sender","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"l2Block","type":"uint256"},{"internalType":"uint256","name":"l1Block","type":"uint256"},{"internalType":"uint256","name":"l2Timestamp","type":"uint256"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"executeTransaction","outputs":[],"stateMutability":"nonpayable","type":"function"}"""
    ),
)
EXECUTE_TRANSACTION_FUNCTION_SIG = function_abi_to_4byte_selector_str(EXECUTE_TRANSACTION_FUNCTION)

ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromBlobs","outputs":[],"stateMutability":"nonpayable","type":"function"}"""
    ),
)
ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION_SIG = function_abi_to_4byte_selector_str(
    ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION
)

ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"name":"data","type":"bytes","internalType":"bytes"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromOrigin","outputs":[],"stateMutability":"nonpayable","type":"function"}"""
    ),
)
ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION_SIG = function_abi_to_4byte_selector_str(
    ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION
)

OUT_BOUND_TRANSFER_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"name":"_l1Token","type":"address","internalType":"address"},{"name":"_to","type":"address","internalType":"address"},{"name":"_amount","type":"uint256","internalType":"uint256"},{"name":"a","type":"uint256","internalType":"uint256"},{"name":"b","type":"uint256","internalType":"uint256"},{"name":"_data","type":"bytes","internalType":"bytes"}],"name":"outboundTransfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}"""
    ),
)
OUT_BOUND_TRANSFER_FUNCTION_SIG = function_abi_to_4byte_selector_str(OUT_BOUND_TRANSFER_FUNCTION)


class ArbType(Enum):

    BRIDGE_NATIVE = 1
    BRIDGE_ERC20 = 2
    BRIDGE_ERC721 = 3

    NORMAL_CROSS_CHAIN_CALL = 7


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
class MessageDeliveredData:
    msg_hash: Optional[str]
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


ZERO_ADDRESS_32 = bytes(32)
ZERO_ADDRESS = bytes(20)


def strip_bytes_leading_zeros(byte_array: bytes) -> bytes:
    if byte_array != ZERO_ADDRESS_32:
        return byte_array.lstrip(b"\x00")
    else:
        return ZERO_ADDRESS


def strip_leading_zeros(hex_str: str) -> str:
    if not hex_str.startswith("0x"):
        raise ValueError(f"hex_str should start with 0x not {hex_str}")
    bs = Web3.to_bytes(hexstr=hex_str)
    bs = strip_bytes_leading_zeros(bs)
    return Web3.to_hex(bs)


def parse_inbox_message_delivered(transaction, contract_set):
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == INBOX_MESSAGE_DELIVERED_EVENT_SIG and log.address in contract_set:
            event = decode_log(INBOX_MESSAGE_DELIVERED_EVENT, log)
            message_num = event["messageNum"]
            ib = InboxMessageDeliveredData(
                transaction_hash=transaction.hash,
                msg_number=message_num,
                data=event["data"],
            )
            res.append(ib)
    return res


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
                block_number=transaction.block_number,
                block_timestamp=transaction.block_timestamp,
                block_hash=transaction.block_hash,
                transaction_hash=transaction.hash,
                from_address=transaction.from_address,
                to_address=transaction.to_address,
                bridge_from_address=sender,
                bridge_to_address=sender,
                extra_info={"fee": baseFeeL1, "kind": kind},
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
                msg_hash=Web3.to_hex(event.get("ticketId")),
                transaction_hash=transaction.hash,
                block_number=transaction.block_number,
                block_timestamp=transaction.block_timestamp,
                block_hash=transaction.block_hash,
                from_address=transaction.from_address,
                to_address=transaction.to_address,
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
    _token = None
    _from = Web3.to_hex(ZERO_ADDRESS)
    _to = Web3.to_hex(ZERO_ADDRESS)
    _amount = 0
    restData = b""
    if not data:
        return selector, _token, _from, _to, _amount, restData
    selector = data[offset : offset + 4]
    offset += 4
    _token = Web3.to_hex(data[offset : offset + 32])
    offset += 32
    _from = Web3.to_hex(data[offset : offset + 32])
    offset += 32
    _to = Web3.to_hex(data[offset : offset + 32])
    offset += 32
    _amount = int.from_bytes(data[offset : offset + 32], "big")
    offset += 32
    restData = Web3.to_hex(data[offset:])
    return selector, _token, _from, _to, _amount, restData


def un_marshal_inbox_message_delivered_data(
    raw_kind,
    data,
    chain_id=Network.Arbitrum.value,
):
    kind = raw_kind
    offset = 0

    if kind == -1:
        kind = data[offset : offset + 1]
        offset += 1

    destAddress = ZERO_ADDRESS
    l2CallValue = 0
    msgValue = 0
    gasLimit = 0
    maxSubmissionCost = 0
    excessFeeRefundAddress = ZERO_ADDRESS
    callValueRefundAddress = ZERO_ADDRESS
    maxFeePerGas = 0
    l1TokenId = None
    l1TokenAmount = 0
    dataBytes = "0x"
    if kind == Constants.INITIALIZATION_MSG_TYPE:
        """
        * bytes memory initMsg = abi.encodePacked(
        * keccak256("ChallengePeriodEthBlocks"),
        * confirmPeriodBlocks,
        * keccak256("SpeedLimitPerSecond"),
        * avmGasSpeedLimitPerBlock / 100, // convert avm gas to arbgas
        * keccak256("ChainOwner"),
        * uint256(uint160(bytes20(owner))),
        * extraConfig
        * );
        */

        """
        chainId = data[offset : offset + 32]
        offset += 32
    elif kind == Constants.L2MessageType_unsignedEOATx:
        gasLimit = data[offset : offset + 32]
        offset += 32
        maxFeePerGas = data[offset : offset + 32]
        offset += 32
        nonce = data[offset : offset + 32]
        offset += 32
        destAddress = data[offset : offset + 32]
        offset += 32
        msgValue = data[offset : offset + 32]
        offset += 32
        dataBytes = Web3.to_hex(data[offset : data.length])
    elif kind == Constants.L2MessageType_unsignedContractTx:
        gasLimit = data[offset : offset + 32]
        offset += 32
        maxFeePerGas = data[offset : offset + 32]
        offset += 32
        destAddress = data[offset : offset + 32]
        offset += 32
        msgValue = data[offset : offset + 32]
        offset += 32
        dataBytes = Web3.to_hex(data[offset : data.length])
    elif kind == Constants.L1MessageType_submitRetryableTx:
        destAddress = Web3.to_hex(data[offset : offset + 32])
        offset += 32
        l2CallValue = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        msgValue = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        maxSubmissionCost = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        excessFeeRefundAddress = Web3.to_hex(data[offset : offset + 32])
        offset += 32
        callValueRefundAddress = Web3.to_hex(data[offset : offset + 32])
        offset += 32
        gasLimit = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        maxFeePerGas = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        dataLength = int.from_bytes(data[offset : offset + 32], "big")
        offset += 32
        # offset += 4
        # l1TokenId = Web3.to_hex(data[offset: offset + 32])
        # offset -= 4
        dataBytes = Web3.to_hex(data[offset : offset + dataLength])

        restData = data[offset:]
        if chain_id == Network.Arbitrum.value:
            if 68 <= len(restData):
                l1TokenAmount = int.from_bytes(restData[36:68], "big")
        elif chain_id == Network.DODO_TESTNET.value:
            if 36 <= len(restData):
                l1TokenId = strip_leading_zeros(Web3.to_hex(restData[4:36]))
            if 100 <= len(restData):
                l1TokenAmount = int.from_bytes(restData[100:132], "big")
    elif kind == Constants.L2_MSG:
        pass
    elif kind == Constants.L1MessageType_batchPostingReport:
        pass
    elif kind == Constants.L1MessageType_ethDeposit:
        destAddress = Web3.to_hex(data[offset : offset + 20])
        offset += 20
        msgValue = int.from_bytes(data[offset : offset + 32], "big")
        l1TokenAmount = msgValue
    else:
        raise Exception(f"uncovered case. kind: {kind}")
    return (
        destAddress,
        l2CallValue,
        msgValue,
        gasLimit,
        maxSubmissionCost,
        excessFeeRefundAddress,
        callValueRefundAddress,
        maxFeePerGas,
        dataBytes,
        l1TokenId,
        l1TokenAmount,
    )


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
                msg_hash=msgNumber,
                l2_block_number=transaction.block_number,
                l2_block_timestamp=transaction.block_timestamp,
                l2_block_hash=transaction.block_hash,
                l2_transaction_hash=transaction.hash,
                l2_from_address=transaction.from_address,
                l2_to_address=transaction.to_address,
                l2_token_address=strip_leading_zeros(_token) if _token else None,
                caller=event.get("caller"),
                destination=event.get("destination"),
                hash=hex(event.get("hash")),
                position=event.get("position"),
                arbBlockNum=event.get("arbBlockNum"),
                ethBlockNum=event.get("ethBlockNum"),
                timestamp=event.get("timestamp"),
                callvalue=amount,
                data=data,
            )
            res.append(l2tol1)
    return res


def parse_sequencer_batch_delivered(transaction, contract_set, transaction_batch_offset) -> list:
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == SEQUENCER_BATCH_DELIVERED_EVENT_SIG and log.address in contract_set:
            input = transaction.input
            input_sig = input[0:10]
            sequenceNumber = 0
            prevMessageCount = 0
            newMessageCount = 0
            gasRefunder = ZERO_ADDRESS
            afterDelayedMessagesRead = 0
            if input_sig == ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION_SIG:
                decoded_input = decode_transaction_data(ADD_SEQUENCER_L2_BATCH_FROM_BLOBS_FUNCTION, input)
                sequenceNumber = decoded_input.get("sequenceNumber")
                prevMessageCount = decoded_input.get("prevMessageCount")
                newMessageCount = decoded_input.get("newMessageCount")
                gasRefunder = decoded_input.get("gasRefunder")
                afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead")

            elif input_sig == ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION_SIG:
                decoded_input = decode_transaction_data(ADD_SEQUENCER_L2_BATCH_FROM_ORIGIN_FUNCTION, transaction.input)
                sequenceNumber = decoded_input.get("sequenceNumber")
                prevMessageCount = decoded_input.get("prevMessageCount")
                newMessageCount = decoded_input.get("newMessageCount")
                gasRefunder = decoded_input.get("gasRefunder")
                afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead")
                data = decoded_input.get("data")
            at = ArbitrumTransactionBatch(
                batch_index=sequenceNumber,
                l1_block_number=transaction.block_number,
                l1_block_timestamp=transaction.block_timestamp,
                l1_block_hash=transaction.block_hash,
                l1_transaction_hash=transaction.hash,
                transaction_count=None,
                end_block_number=newMessageCount + transaction_batch_offset,
                start_block_number=prevMessageCount + transaction_batch_offset,
            )
            res.append(at)
    return res


def parse_node_confirmed(transaction, contract_set) -> list:
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == NODE_CONFIRMED_EVENT_SIG and log.address in contract_set:
            event = decode_log(NODE_CONFIRMED_EVENT, log)
            res.append(
                ArbitrumStateBatchConfirmed(
                    node_num=event.get("nodeNum"),
                    block_hash=Web3.to_hex(event.get("blockHash")),
                    send_root=Web3.to_hex(event.get("sendRoot")),
                    l1_block_number=transaction.block_number,
                    l1_block_timestamp=transaction.block_timestamp,
                    l1_block_hash=transaction.block_hash,
                    l1_transaction_hash=transaction.hash,
                    start_block_number=None,
                    end_block_number=None,
                    transaction_count=None,
                )
            )
    return res


def parse_node_created(transaction, contract_set) -> list:
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == NODE_CREATED_EVENT_SIG and log.address in contract_set:
            res.append(
                ArbitrumStateBatchCreated(
                    node_num=int(log.topic1, 16),
                    create_l1_block_number=transaction.block_number,
                    create_l1_block_timestamp=transaction.block_timestamp,
                    create_l1_block_hash=transaction.block_hash,
                    create_l1_transaction_hash=transaction.hash,
                    parent_node_hash=log.topic2,
                    node_hash=log.topic3,
                )
            )
    return res


def parse_bridge_token(transaction, contract_set) -> list:
    res = []
    l1_token_address = None
    l2_token_address = None
    if transaction.to_address in contract_set:
        for log in transaction.receipt.logs:
            if log.topic0 == BEACON_UPGRADED_EVENT_SIG:
                l2_token_address = log.address
            if log.topic0 == DEPOSIT_FINALIZED_EVENT_SIG:
                l1_token_address = log.topic1
        l1_token_address = l1_token_address
        l2_token_address = l2_token_address
        if l1_token_address and l2_token_address:
            res.append(
                BridgeToken(
                    l1_token_address=l1_token_address,
                    l2_token_address=l2_token_address,
                )
            )
    return res


def parse_outbound_transfer_function(transactions, contract_set):
    res = []
    for tnx in transactions:
        if tnx.to_address in contract_set:
            input_sig = tnx.input[0:10]
            if input_sig == OUT_BOUND_TRANSFER_FUNCTION_SIG:
                decoded_input = decode_transaction_data(OUT_BOUND_TRANSFER_FUNCTION, tnx.input)
                res.append(
                    TransactionToken(
                        transaction_hash=tnx.hash,
                        l1Token=decoded_input["_l1Token"],
                        amount=decoded_input["_amount"],
                    )
                )
    return res


def parse_bridge_call_triggered(transaction, contract_set):
    res = []
    for log in transaction.receipt.logs:
        if log.topic0 == BRIDGE_CALL_TRIGGERED_EVENT_SIG and log.address in contract_set:
            decoded_input = decode_transaction_data(EXECUTE_TRANSACTION_FUNCTION, transaction.input)
            msg_num = decoded_input["index"]
            event = decode_log(BRIDGE_CALL_TRIGGERED_EVENT, log)
            res.append(
                BridgeCallTriggeredData(
                    msg_hash=msg_num,
                    l1_transaction_hash=transaction.hash,
                    l1_block_number=transaction.block_number,
                    l1_block_timestamp=transaction.block_timestamp,
                    l1_block_hash=transaction.block_hash,
                    l1_from_address=transaction.from_address,
                    l1_to_address=transaction.to_address,
                    outbox=event.get("outbox"),
                    to=event.get("to"),
                    value=event.get("value"),
                    data=event.get("data"),
                )
            )
    return res
