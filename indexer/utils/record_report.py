#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 下午3:22
Author  : xuzh
Project : hemera_indexer
"""

from eth_account import Account
from web3 import Web3

from common.utils.format_utils import hex_str_to_bytes
from common.utils.web3_utils import to_checksum_address
from indexer.utils.abi_setting import SUBMIT_INDEX_FUNCTION


class RecordReporter:
    contract_address = ""

    def __init__(self, private_key, from_address):
        self.web3 = Web3(Web3.HTTPProvider("https://1rpc.io/holesky"))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.from_address = from_address
        self.contract = self.web3.eth.contract(
            address=to_checksum_address("0xf3d02049dfbcb220162ce2071d443929549eea19"),
            abi=[SUBMIT_INDEX_FUNCTION.get_abi()],
        )
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)

    def report(self, chain_id: int, start_block: int, end_block: int, indexed_data: dict):
        formatted_indexed_data = []
        for data in indexed_data:
            # 确保每个字符串都是32字节
            data_class = data["dataClass"].encode("utf-8").rjust(32, b"\x00")
            code_hash = hex_str_to_bytes(data["codeHash"]).rjust(32, b"\x00")
            count = data["count"]
            data_hash = hex_str_to_bytes(data["dataHash"]).rjust(32, b"\x00")

            formatted_indexed_data.append((data_class, code_hash, count, data_hash))

        transaction = self.contract.functions.submitIndexRecord(
            chain_id, start_block, end_block, formatted_indexed_data
        ).build_transaction(
            {
                "from": to_checksum_address(self.from_address),
                "nonce": self.nonce,
            }
        )

        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)

        # emit transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        self.nonce = self.nonce + 1


if __name__ == "__main__":
    reporter = RecordReporter(
        from_address="0xfdeacf567997fc153e2fe1de098aeedc71294b71",
        private_key="0x0f0dca973a687bfcbabdd85fad3bce5d49593300771eda9cda07bf9397d17488",
    )

    indexed_data = [
        {"dataClass": "block", "codeHash": "4ac520fc", "count": 1, "dataHash": "4ac520fc"},
        {"dataClass": "block", "codeHash": "4ac520fc", "count": 1, "dataHash": "4ac520fc"},
    ]

    reporter.report(chain_id=1, start_block=10000, end_block=10001, indexed_data=indexed_data)
