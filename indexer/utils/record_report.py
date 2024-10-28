#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 下午3:22
Author  : xuzh
Project : hemera_indexer
"""
import asyncio
import logging
import threading
from queue import Empty, Queue

from eth_account import Account
from web3 import Web3
from web3.exceptions import TimeExhausted

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from common.utils.web3_utils import to_checksum_address
from indexer.domain import DomainMeta
from indexer.utils.abi_setting import REGISTER_FEATURE_FUNCTION, SUBMIT_INDEX_FUNCTION


class AsyncTransactionSubmitter:

    def __init__(self, web3, account):
        self.web3 = web3
        self.account = account
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)

        self.max_retries = 5
        self.retry_delay = 5
        self.receipt_timeout = 30
        self.receipt_poll_latency = 2

        self.submit_thread = None
        self.transaction_queue = Queue()
        self.running = False
        self.logger = logging.getLogger(__name__)

    def start(self):
        if self.submit_thread is None:
            self.running = True
            self.submit_thread = threading.Thread(target=self._run_async_submitter)
            self.submit_thread.daemon = False
            self.submit_thread.start()
            self.logger.info("Submit thread started.")
        else:
            self.logger.info("Submit thread already started.")

    def stop(self):
        self.running = False
        if self.submit_thread:
            self.submit_thread.join(timeout=self.receipt_timeout)
            self.submit_thread = None
            self.logger.info("Submit thread stopped.")
        else:
            self.logger.info("Submit thread already stopped.")

    def set_transaction(self, info):
        self.transaction_queue.put(info)

    def _run_async_submitter(self):
        asyncio.run(self._queue_check_and_process())

    async def _queue_check_and_process(self):
        while self.running:
            try:
                try:
                    info = self.transaction_queue.get_nowait()
                    success = await self._process_transaction(info)
                    self.transaction_queue.task_done()

                    if not success:
                        # todo message store in db
                        pass

                except Empty as e:
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                self.logger.error(f"Submit transaction failed. {e}")

    async def _process_transaction(self, info: dict) -> bool:
        builder = info["transaction_builder"]
        parameters = info["transaction_parameters"]

        self.logger.info(f"Processing transaction with parameters: {parameters}")

        self.nonce = (
            self.nonce if self.web3.eth.get_transaction_count(self.account.address) < self.nonce else self.nonce
        )

        for entire_retry in range(self.max_retries):
            for submit_retry in range(self.max_retries):
                try:
                    parameters["nonce"] = self.nonce
                    signed_txn = builder(**parameters)
                    txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    self.logger.info(
                        f"Submitted transaction {signed_txn} successfully with parameter: {parameters}.\n"
                        f"Waiting for receipt."
                    )

                except ValueError as e:
                    if str(e).find("nonce too low") != -1:
                        self.nonce = self.nonce + 1
                        continue

                except Exception as e:
                    self.logger.error(f"Building and submitting transaction failed. {e}")
                    await asyncio.sleep(self.retry_delay)
                    continue

            for receipt_retry in range(self.max_retries):
                try:
                    receipt = self.web3.eth.wait_for_transaction_receipt(
                        txn_hash, timeout=self.receipt_timeout, poll_latency=self.receipt_poll_latency
                    )

                    if receipt["status"] == 1:
                        self.logger.info(f"Transaction {bytes_to_hex_str(txn_hash)} had been receipted.")
                        return True
                    else:
                        self.logger.error(
                            f"Transaction: {bytes_to_hex_str(txn_hash)} failed. \n"
                            f"with info: {parameters}\n"
                            f"Receipt: {receipt}"
                        )

                        break
                except TimeExhausted as e:
                    self.logger.warning(
                        f"Transaction: {bytes_to_hex_str(txn_hash)} is not in the chain after "
                        f"{self.receipt_timeout * (receipt_retry + 1)} seconds. \n"
                        f"Reporter will continue to retry waiting for receipt "
                        f"{self.max_retries - receipt_retry - 1} times, {self.receipt_timeout} seconds each time.\n."
                    )
                    receipt = None
                    continue

            if receipt is None or receipt["status"] == 0:
                self.logger.warning(
                    f"Transaction: {bytes_to_hex_str(txn_hash)} had not been receipted by chain. \n"
                    f"Reporter will retry to submit the transaction with info: {parameters}. \n "
                )
                await asyncio.sleep(self.retry_delay)

        return False


class RecordReporter:

    def __init__(self, private_key, from_address):
        self.web3 = Web3(Web3.HTTPProvider("https://1rpc.io/holesky"))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.from_address = from_address
        self.contract = self.web3.eth.contract(
            address=to_checksum_address("0xB0c42250F0A3D141aD25e5B6A162ddbd5CAE7ec5"),
            abi=[SUBMIT_INDEX_FUNCTION.get_abi()],
        )
        self.transaction_submitter = AsyncTransactionSubmitter(web3=self.web3, account=self.account)
        self.transaction_submitter.start()
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)

    def report(self, chain_id: int, start_block: int, end_block: int, runtime_code_hash: str, indexed_data: dict):
        def transaction_builder(
            chain_id: int, start_block: int, end_block: int, runtime_code_hash: str, indexed_data: dict, nonce: int
        ):
            code_hash = hex_str_to_bytes(runtime_code_hash).rjust(32, b"\x00")

            formatted_indexed_data = []
            for data in indexed_data:
                # 确保每个字符串都是32字节
                data_class = hex_str_to_bytes(data["dataClass"]).rjust(4, b"\x00")
                count = data["count"]
                data_hash = hex_str_to_bytes(data["dataHash"]).rjust(32, b"\x00")

                formatted_indexed_data.append((data_class, count, data_hash))

            transaction = self.contract.functions.submitIndexRecord(
                chain_id, start_block, end_block, code_hash, formatted_indexed_data
            ).build_transaction(
                {
                    "from": to_checksum_address(self.from_address),
                    "nonce": nonce,
                }
            )

            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            return signed_txn

        transaction_parameters = {
            "chain_id": chain_id,
            "start_block": start_block,
            "end_block": end_block,
            "runtime_code_hash": runtime_code_hash,
            "indexed_data": indexed_data,
        }

        self.transaction_submitter.set_transaction(
            {
                "transaction_builder": transaction_builder,
                "transaction_parameters": transaction_parameters,
            }
        )


class FeatureRegister:
    def __init__(self, private_key, from_address):
        self.web3 = Web3(Web3.HTTPProvider("https://1rpc.io/holesky"))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.from_address = from_address
        self.contract = self.web3.eth.contract(
            address=to_checksum_address("0xB0c42250F0A3D141aD25e5B6A162ddbd5CAE7ec5"),
            abi=[REGISTER_FEATURE_FUNCTION.get_abi()],
        )
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)

    def register_all(self):
        code_hashes = DomainMeta._code_integrity

        dataclass_list = []
        code_hash_list = []
        for dataclass_hash in code_hashes.keys():
            # for dataclass_hash in ['67a70c90', '6048a7e2', '718c3b53']:
            dataclass = hex_str_to_bytes(dataclass_hash).rjust(4, b"\x00")
            # code_hash = hex_str_to_bytes(code_hashes[dataclass_hash]).rjust(32, b"\x00")
            commit_hash = hex_str_to_bytes("01378141092f991934d484d0c8a567bfe3cd958d").rjust(32, b"\x00")

            dataclass_list.append(dataclass)
            # code_hash_list.append(code_hash)
            code_hash_list.append(commit_hash)

        self.nonce = (
            self.nonce if self.web3.eth.get_transaction_count(self.account.address) < self.nonce else self.nonce
        )

        transaction = self.contract.functions.registerFeature(dataclass_list, code_hash_list).build_transaction(
            {
                "from": to_checksum_address(self.from_address),
                "nonce": self.nonce,
            }
        )

        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)

        # emit transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        self.nonce = self.nonce + 1

    def register_one(self, dataclass_hash: str):

        code_hashes = DomainMeta._code_integrity

        if dataclass_hash not in code_hashes:
            raise ValueError(
                f"Register action failed. Probably reasons come from the following:\n"
                f"1) You should use hash code of dataclass to register.\n"
                f"2) {dataclass_hash} is not a valid hash code, it cannot match any dataclass"
            )

        dataclass = hex_str_to_bytes(dataclass_hash).rjust(4, b"\x00")

        # code_hash = hex_str_to_bytes(code_hashes[dataclass_hash]).rjust(32, b"\x00")
        commit_hash = hex_str_to_bytes("01378141092f991934d484d0c8a567bfe3cd958d").rjust(32, b"\x00")

        self.nonce = (
            self.nonce if self.web3.eth.get_transaction_count(self.account.address) < self.nonce else self.nonce
        )

        transaction = self.contract.functions.registerFeature([dataclass], [commit_hash]).build_transaction(
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
    pass
