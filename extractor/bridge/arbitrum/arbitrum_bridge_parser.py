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
from web3._utils.contracts import decode_transaction_data

from domain.transaction import format_transaction_data
from extractor.signature import decode_log
from extractor.types import dict_to_dataclass, Transaction, Log, Receipt

logger = logging.getLogger(__name__)


class ArbitrumBridgeExtractor:

    def __init__(self):
        pass

    def l1_contract_extractor(self, transactions) -> list:
        res = []
        tnx_input = self.parseOutboundTransferFunction(transactions)
        tnx_map = {}
        for tnx in tnx_input:
            tnx_map[tnx['hash']] = tnx

        message_delivered_event_list = []
        for tnx in transactions:

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
    # l2Rpc = "https://dodochain-testnet.alt.technology"
    l2Rpc = "https://arbitrum-one-rpc.publicnode.com"
    # l1Rpc = "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
    l1Rpc = "https://ethereum-rpc.publicnode.com"
    l1w3 = Web3(Web3.HTTPProvider(l1Rpc))
    l2w3 = Web3(Web3.HTTPProvider(l2Rpc))

    # L1 -> L2
    # tnx = getL1Transaction(46298492, "0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0", l1Rpc)
    l1tnx = "0xdb88244fe9d6e078d60dda68dd81dc29d1094a19ad84d9da42aecdf5591718d1"
    tnx = l1w3.eth.get_transaction(l1tnx)
    receipt = l1w3.eth.get_transaction_receipt(l1tnx)
    # logs = [dict_to_dataclass(ll, Log) for ll in receipt.logs]
    # receipt = dict_to_dataclass(receipt, Receipt)
    # receipt.logs = logs

    transaction = dict_to_dataclass(format_transaction_data(tnx), Transaction)
    transaction.receipt = receipt
    l2tnx = "0x51a14b1b6fcb89239781eaa387c7a919ea744f3e641ae01a6367b8d54fa452d8"

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
