#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/9 10:05
# @Author  will
# @File  arb_bridge.py
# @Brief
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, cast

from eth_typing import ABIEvent, ABIFunction
from web3 import Web3

from domain.transaction import format_transaction_data
from extractor.signature import decode_log
from extractor.types import dict_to_dataclass, Transaction, Log, Receipt

logger = logging.getLogger(__name__)


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
    msg_hash: bytes
    block_number: int
    block_timestamp: int
    block_hash: bytes
    transaction_hash: bytes
    from_address: bytes
    to_address: bytes
    bridge_from_address: bytes
    bridge_to_address: bytes
    extra_info: Dict[str, Any]
    beforeInboxAcc: bytes
    messageIndex: int
    inbox: bytes
    kind: int
    sender: bytes
    messageDataHash: bytes
    baseFeeL1: int
    timestamp: int


@dataclass
class InboxMessageDeliveredData:
    transaction_hash: str
    msg_number: int
    data: bytes


@dataclass
class TicketCreatedData:
    msg_hash: bytes
    transaction_hash: bytes
    block_number: int
    block_timestamp: int
    block_hash: bytes
    from_address: bytes
    to_address: bytes


@dataclass
class BridgeCallTriggeredData:
    msg_hash: bytes
    l1_transaction_hash: bytes
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: bytes
    l1_from_address: bytes
    l1_to_address: bytes
    outbox: bytes
    to: bytes
    value: int
    data: bytes


@dataclass
class L2ToL1Tx_64:
    msg_hash: bytes
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: bytes
    l2_transaction_hash: bytes
    l2_from_address: bytes
    l2_to_address: bytes
    l2_token_address: bytes
    caller: bytes
    destination: bytes
    hash: bytes
    position: int
    arbBlockNum: int
    ethBlockNum: int
    timestamp: int
    callvalue: int
    data: bytes


@dataclass
class TransactionToken:
    transaction_hash: str
    l1Token: bytes
    amount: int


ZERO_ADDRESS_32 = bytes(32)
ZERO_ADDRESS = bytes(20)


def strip_leading_zeros(byte_array: bytes) -> bytes:
    if byte_array != ZERO_ADDRESS_32:
        return byte_array.lstrip(b'\x00')
    else:
        return ZERO_ADDRESS


class ArbAbiClass:
    MessageDeliveredEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageIndex","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeInboxAcc","type":"bytes32"},{"indexed":false,"internalType":"address","name":"inbox","type":"address"},{"indexed":false,"internalType":"uint8","name":"kind","type":"uint8"},{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"bytes32","name":"messageDataHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"baseFeeL1","type":"uint256"},{"indexed":false,"internalType":"uint64","name":"timestamp","type":"uint64"}],"name":"MessageDelivered","type":"event"}"""))

    InboxMessageDeliveredEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageNum","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"InboxMessageDelivered","type":"event"}"""))

    BridgeCallTriggeredEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"outbox","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"BridgeCallTriggered","type":"event"}"""))

    WithdrawalInitiatedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"l1Token","type":"address"},{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_l2ToL1Id","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_exitNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"WithdrawalInitiated","type":"event"}"""))

    TicketCreatedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"ticketId","type":"bytes32"}],"name":"TicketCreated","type":"event"}"""))

    TxToL1_GW_Event = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_from","type":"address"},{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_id","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"_data","type":"bytes"}],"name":"TxToL1","type":"event"}"""))

    L2ToL1Tx_64_Event = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"destination","type":"address"},{"indexed":true,"internalType":"uint256","name":"hash","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"position","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"arbBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"ethBlockNum","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"timestamp","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"callvalue","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"L2ToL1Tx","type":"event"}"""))

    ExecuteTransactionFunction = cast(ABIFunction, json.loads(
        """{"inputs":[{"internalType":"bytes32[]","name":"proof","type":"bytes32[]"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"address","name":"l2Sender","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"l2Block","type":"uint256"},{"internalType":"uint256","name":"l1Block","type":"uint256"},{"internalType":"uint256","name":"l2Timestamp","type":"uint256"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"executeTransaction","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))

    SequencerBatchDeliveredEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"batchSequenceNumber","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"beforeAcc","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"afterAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"delayedAcc","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"components":[{"internalType":"uint64","name":"minTimestamp","type":"uint64"},{"internalType":"uint64","name":"maxTimestamp","type":"uint64"},{"internalType":"uint64","name":"minBlockNumber","type":"uint64"},{"internalType":"uint64","name":"maxBlockNumber","type":"uint64"}],"indexed":false,"internalType":"struct IBridge.TimeBounds","name":"timeBounds","type":"tuple"},{"indexed":false,"internalType":"enum IBridge.BatchDataLocation","name":"dataLocation","type":"uint8"}],"name":"SequencerBatchDelivered","type":"event"}"""))

    AddSequencerL2BatchFromBlobsFunction = cast(ABIFunction, json.loads(
        """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromBlobs","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))

    AddSequencerL2BatchFromOriginFunction = cast(ABIFunction, json.loads(
        """{"inputs":[{"internalType":"uint256","name":"sequenceNumber","type":"uint256"},{"name":"data","type":"bytes","internalType":"bytes"},{"internalType":"uint256","name":"afterDelayedMessagesRead","type":"uint256"},{"internalType":"contract IGasRefunder","name":"gasRefunder","type":"address"},{"internalType":"uint256","name":"prevMessageCount","type":"uint256"},{"internalType":"uint256","name":"newMessageCount","type":"uint256"}],"name":"addSequencerL2BatchFromOrigin","outputs":[],"stateMutability":"nonpayable","type":"function"}"""))

    NodeCreatedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":true,"internalType":"bytes32","name":"parentNodeHash","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"nodeHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"executionHash","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"beforeState","type":"tuple"},{"components":[{"components":[{"internalType":"bytes32[2]","name":"bytes32Vals","type":"bytes32[2]"},{"internalType":"uint64[2]","name":"u64Vals","type":"uint64[2]"}],"internalType":"struct GlobalState","name":"globalState","type":"tuple"},{"internalType":"enum MachineStatus","name":"machineStatus","type":"uint8"}],"internalType":"struct RollupLib.ExecutionState","name":"afterState","type":"tuple"},{"internalType":"uint64","name":"numBlocks","type":"uint64"}],"indexed":false,"internalType":"struct RollupLib.Assertion","name":"assertion","type":"tuple"},{"indexed":false,"internalType":"bytes32","name":"afterInboxBatchAcc","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"wasmModuleRoot","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"inboxMaxCount","type":"uint256"}],"name":"NodeCreated","type":"event"}"""))
    # NodeCreatedEvent.signatrue = ("0x4f4caa9e67fb994e349dd35d1ad0ce23053d4323f83ce11dc817b5435031d096")
    NodeCreatedEventSignature = "0x4f4caa9e67fb994e349dd35d1ad0ce23053d4323f83ce11dc817b5435031d096"

    NodeConfirmedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint64","name":"nodeNum","type":"uint64"},{"indexed":false,"internalType":"bytes32","name":"blockHash","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"sendRoot","type":"bytes32"}],"name":"NodeConfirmed","type":"event"}"""))
    NodeConfirmedEventSignature = "0x22ef0479a7ff660660d1c2fe35f1b632cf31675c2d9378db8cec95b00d8ffa3c"

    BeaconUpgradedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"beacon","type":"address"}],"name":"BeaconUpgraded","type":"event"}"""))

    DepositFinalizedEvent = cast(ABIEvent, json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"receiver","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"DepositFinalized","type":"event"}"""))
    OutboundTransferFunction = cast(ABIFunction, json.loads(
        """{"inputs":[{"name":"_l1Token","type":"address","internalType":"address"},{"name":"_to","type":"address","internalType":"address"},{"name":"_amount","type":"uint256","internalType":"uint256"},{"name":"a","type":"uint256","internalType":"uint256"},{"name":"b","type":"uint256","internalType":"uint256"},{"name":"_data","type":"bytes","internalType":"bytes"}],"name":"outboundTransfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}"""))


class ArbitrumBridgeExtractor:

    def __init__(self):
        pass

    def l1_contract_extractor(self):
        pass

    def l2_contract_extractor(self):
        pass

    def batch_extractor(self, transactions, contract_list):
        tnx_batches = map(transactions, self.parseSequencerBatchDelivered)
        pass

    def parseTicketCreatedEvent(self, transaction, contract_list):
        res = []
        for log in transaction.receipt.logs:
            if log.topic0 == ArbAbiClass.TicketCreatedEvent.signature and log.address in contract_list:
                event = decode_log(ArbAbiClass.TicketCreatedEvent, log)
                tc = TicketCreatedData(
                    msg_hash=event.get("ticketId"),
                    transaction_hash=Web3.to_bytes(transaction.hash),
                    block_number=transaction.blockNumber,
                    block_timestamp=transaction.blockTimestamp,
                    block_hash=Web3.to_bytes(transaction.blockHash),
                    from_address=Web3.to_bytes(transaction.fromAddress),
                    to_address=Web3.to_bytes(transaction.toAddress),
                )
                res.append(tc)
        return res

    def parseSequencerBatchDelivered(self, transaction, contract_list) -> list:
        res = []
        for log in transaction.receipt.logs:
            if log.topic == ArbAbiClass.SequencerBatchDeliveredEvent.signature and log.address in contract_list:
                addSeqBlobSig = ArbAbiClass.AddSequencerL2BatchFromBlobsFunction.signature.slice(0, 10)
                addSeqOriginSig = ArbAbiClass.AddSequencerL2BatchFromOriginFunction.signature.slice(0, 10)
                input = transaction.input
                input_sig = input.slice(0, 10)
                sequenceNumber = 0
                prevMessageCount = 0
                newMessageCount = 0
                gasRefunder = ZERO_ADDRESS
                afterDelayedMessagesRead = 0
                if (input_sig == addSeqBlobSig):
                    decoded_input = decode_input(ArbAbiClass.AddSequencerL2BatchFromBlobsFunction, input)
                    sequenceNumber = decoded_input.get("sequenceNumber").getOrElse(None).toString.toLong
                    prevMessageCount = decoded_input.get("prevMessageCount").getOrElse(None).toString.toLong
                    newMessageCount = decoded_input.get("newMessageCount").getOrElse(None).toString.toLong
                    gasRefunder = Web3.to_bytes(decoded_input.get("gasRefunder").getOrElse("").toString)
                    afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead").getOrElse(
                        None).toString.toLong

                elif (input_sig == addSeqOriginSig):
                    decoded_input = decode_input(ArbAbiClass.AddSequencerL2BatchFromOriginFunction, transaction.input)
                    sequenceNumber = decoded_input.get("sequenceNumber").getOrElse(None).toString.toLong
                    prevMessageCount = decoded_input.get("prevMessageCount").getOrElse(None).toString.toLong
                    newMessageCount = decoded_input.get("newMessageCount").getOrElse(None).toString.toLong
                    gasRefunder = Web3.to_bytes(decoded_input.get("gasRefunder").getOrElse("").toString)
                    afterDelayedMessagesRead = decoded_input.get("afterDelayedMessagesRead").getOrElse(
                        None).toString.toLong
                    data = decoded_input.get("data")
                at = ArbitrumTransactionBatch()
                res.append(at)
        return res

    def parseNodeConfirmed(self, transaction, contract_list) -> list:
        res = []
        for log in transaction.receipt.logs:
            if log.topic0 == ArbAbiClass.NodeConfirmedEvent.signature and log.address in contract_list:
                event = decode_log(ArbAbiClass.NodeConfirmedEvent, log)
                asb = ArbitrumStateBatchConfirmed(
                    node_num=event.get("nodeNum").toString.toLong,
                    block_hash="0x" + bytesToHex(event.get("blockHash").asInstanceOf[Array[Byte]]),
                    send_root="0x" + bytesToHex(event.get("sendRoot").asInstanceOf[Array[Byte]]),
                    l1_block_number=transaction.blockNumber,
                    l1_block_timestamp=transaction.blockTimestamp,
                    l1_block_hash=transaction.blockHash,
                    l1_transaction_hash=transaction.hash,
                )
                res.append(asb)
        return res

    def parseNodeCreated(self, transaction, contract_list) -> list:
        res = []
        for log in transaction.receipt.logs:
            if log.topic0 == ArbAbiClass.NodeCreatedEvent.signature and log.add_address in contract_list:
                event = decode_log(ArbAbiClass.NodeCreatedEvent, log)
                asb = ArbitrumStateBatchCreated(
                    node_num=bytesToLong(hexStringToBytes(log.topic1)),
                    create_l1_block_number=transaction.blockNumber,
                    create_l1_block_timestamp=transaction.blockTimestamp,
                    create_l1_block_hash=transaction.blockHash,
                    create_l1_transaction_hash=transaction.hash,
                    parent_node_hash=log.topic2,
                    node_hash=log.topic3
                )
                res.append(asb)
        return res

    def parseBridgeToken(self, transaction, contract_list) -> list:
        res = []
        l1_token_address = None
        l2_token_address = None
        if transaction.topic1 in contract_list:
            for log in transaction.receipt.logs:
                if (log.topic0 == ArbAbiClass.BeaconUpgradedEvent.signature):
                    l2_token_address = log.add_address
                if log.topic0 == ArbAbiClass.DepositFinalizedEvent.signature:
                    l1_token_address = log.topic1
            l1_token_address = strip_leading_zeros(Web3.to_bytes(l1_token_address))
            l2_token_address = strip_leading_zeros(Web3.to_bytes(l2_token_address))
            if l1_token_address and l2_token_address:
                br = BridgeToken()
                res.append(br)
        return res

    def parseOutboundTransferFunction(self, transactions, contract_list) -> list:
        res = []
        for tnx in transactions:
            if tnx.to_address in contract_list and tnx.input[0:10] == ArbAbiClass.OutboundTransferFunction.signature[
                                                                      0:10]:
                decoded_input = decode_input(ArbAbiClass.OutboundTransferFunction, tnx.input)
                tt = TransactionToken(
                    transaction_hash=tnx.hash,
                    l1Token=Web3.to_bytes(decoded_input.get("_l1Token").toString),
                    amount=(decoded_input.get("_amount").getOrElse(None).toString)
                )
                res.append(tt)
        return res


def get_formated_transaction(rpc, tnx_hash):
    pass


def main():

    # postgres = PostgresqlDatabaseUtils.parseFromURL("")

    l2Rpc = "https://dodochain-testnet.alt.technology"
    l1Rpc = "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
    l1w3 = Web3(Web3.HTTPProvider(l1Rpc))
    l2w3 = Web3(Web3.HTTPProvider(l2Rpc))

    # L1 -> L2
    # tnx = getL1Transaction(46298492, "0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0", l1Rpc)
    tnx = l1w3.eth.get_transaction('0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0')
    receipt = l1w3.eth.get_transaction_receipt('0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0')
    # logs = [dict_to_dataclass(ll, Log) for ll in receipt.logs]
    # receipt = dict_to_dataclass(receipt, Receipt)
    # receipt.logs = logs

    transaction = dict_to_dataclass(format_transaction_data(tnx), Transaction)
    transaction.receipt = receipt

    # obj = ArbitrumL1ContractExtractor(
    #     ["0xc0856971702b02a5576219540bd92dae79a79288", "0xd62ef8d8c71d190417c6ce71f65795696c069f09",
    #      "0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d", "0xe3661c8313b35ba310ad89e113561f3c983dc761"], l1Rpc)
    # data = obj.extract([tnx])
    # print(data)
    # for x in filter(None, data):
    #     postgres.saveToPostgres(x)
    #
    # # L2 -> L1
    # tnx2 = getL2Transaction(18, "0x023026939dcbab09a40ca8e83a612bcf280e7fb6f6e4a505b04e2d23b7274648", l2Rpc)
    # obj2 = ArbitrumL2ContractExtractor(
    #     ["0x000000000000000000000000000000000000006e", "0x0000000000000000000000000000000000000064",
    #      "0x00000000000000000000000000000000000a4b05"], l2Rpc)
    # data2 = obj2.extract([tnx2])
    # print(data2)
    # for x in filter(None, data2):
    #     postgres.saveToPostgres(x)
    #
    # # L2 -> L1 (l1confirm)
    # tnx3 = getL2Transaction(37326739, "0xfea97317e8533d6a0cc3ef49c75a40439793057c3b0f6a414ab3dd57efccb06e", l1Rpc)
    # obj3 = ArbitrumL1ContractExtractor(["0xc0856971702b02a5576219540bd92dae79a79288"], l1Rpc)
    # data3 = obj3.extract([tnx3])
    # print(data3)
    # for x in filter(None, data3):
    #     postgres.saveToPostgres(x)
    #
    # # L1 -> L2 (transaction_batch)
    # tnx4 = getL1Transaction(52092275, "0xe162dc25c9da007aeb0c0efaf62eb1a601902b3b2ddcbe9c6dd8b7856004e35c", l1Rpc)
    # obj4 = ArbitrumBatchExtractor(["0x67ad6c79e33ea9e523e0e68961456d0ac7a973cc"], l1Rpc)
    # data4 = obj4.extract([tnx4])
    # print(data4)
    # for x in filter(None, data4):
    #     postgres.saveToPostgres(x)
    #
    # # L1 -> L2 (state_batch)
    # tnx5 = getL1Transaction(37292172, "0xb8b70706030a7a3ace5377b969104e5dd1435a89cef163522f008faa4e277e36", l1Rpc)
    # tnx6 = getL1Transaction(37299605, "0x4dda2b921ca2a4408c74a3b600d08dcf19f1565be8a9990fe5baa6e0da0e22ac", l1Rpc)
    # obj5 = ArbitrumBatchExtractor(
    #     ["0xc475f82504ca2aaec3c966bddb19a5c738f22c46", "0x297c7b1bbe30353de62936b6722894fca2d1010e",
    #      "0x67ad6c79e33ea9e523e0e68961456d0ac7a973cc", "0xaeb5fe2f7003881c3a8ebae9664e8607f3935d53",
    #      "0xbc4cc964ef0ea5792a398f9e738edf368a34f003"], l1Rpc)
    # data5 = obj5.extract([tnx5, tnx6])
    # print(data5)
    # for x in filter(None, data5):
    #     postgres.saveToPostgres(x)
    pass

if __name__ == '__main__':
    main()
