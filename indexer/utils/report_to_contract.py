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
from concurrent import futures
from datetime import datetime, timezone

from eth_account import Account
from sqlalchemy import insert, update
from web3 import Web3
from web3.exceptions import TimeExhausted

from common.models.report_records import ReportRecords, ReportStatus
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from common.utils.web3_utils import to_checksum_address
from indexer.domain import DomainMeta
from indexer.utils.abi_setting import REGISTER_FEATURE_FUNCTION, SUBMIT_INDEX_FUNCTION

REQUEST_RPC = "https://1rpc.io/holesky"
CONTRACT_ADDRESS = to_checksum_address("0xB0c42250F0A3D141aD25e5B6A162ddbd5CAE7ec5")


class AsyncTransactionSubmitter:

    def __init__(self, web3, account, service):
        self.max_retries = 5
        self.retry_delay = 5
        self.receipt_timeout = 30
        self.receipt_poll_latency = 2
        self.max_concurrent = 50

        self.web3 = web3
        self.account = account
        self.service = service
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)
        self.nonce_lock = None

        self.running = False
        self.thread_pool = None
        self.loop_thread = None
        self.event_loop = None
        self.loop_ready = threading.Event()

        self.logger = logging.getLogger(__name__)

    def start(self):
        if not self.running:
            self.running = True
            self.loop_thread = threading.Thread(target=self._run_event_loop)
            self.loop_thread.daemon = False
            self.loop_thread.start()

            self.loop_ready.wait()
            self.logger.info("Transaction submitter started.")
        else:
            self.logger.info("Transaction submitter already started.")

    def _run_event_loop(self):
        try:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)

            self.nonce_lock = asyncio.Lock(loop=self.event_loop)
            self.thread_pool = futures.ThreadPoolExecutor(
                max_workers=self.max_concurrent, thread_name_prefix="Web3Worker"
            )

            self.loop_ready.set()

            self.event_loop.run_forever()
        finally:
            self.thread_pool.shutdown(wait=True)
            self.event_loop.close()
            self.logger.info("Event loop closed.")

    def stop(self):
        if self.running:
            self.running = False
            if self.event_loop and self.loop_thread:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                self.loop_thread.join()
                self.loop_thread = None
            self.logger.info("Transaction submitter stopped.")
        else:
            self.logger.info("Transaction submitter already stopped.")

    def set_transaction(self, info):

        def _handle_future_result(future):
            try:
                future.result()
            except Exception as e:
                self.logger.error(f"Transaction processing failed: {e}")

        if not self.running:
            raise RuntimeError("Transaction submitter not running.")

        feature = asyncio.run_coroutine_threadsafe(self._process_transaction(info), self.event_loop)
        feature.add_done_callback(_handle_future_result)
        self.logger.info("Transaction submitted to processing queue")

    async def submit_record_to_db(self, info, transaction_hash=None, report_from=None):
        session = self.service.get_service_session()

        try:
            stmt = insert(ReportRecords).values(
                {
                    "chain_id": info["chain_id"],
                    "mission_type": report_from,
                    "start_block_number": info["start_block"],
                    "end_block_number": info["end_block"],
                    "runtime_code_hash": hex_str_to_bytes(info["runtime_code_hash"]),
                    "report_details": info["indexed_data"],
                    "transaction_hash": transaction_hash,
                }
            )
            result = session.execute(stmt)
            session.commit()
        finally:
            session.close()
        return result.inserted_primary_key[0]

    async def update_report_status(self, report_id, report_status, exception=None):
        session = self.service.get_service_session()
        try:
            stmt = (
                update(ReportRecords)
                .where(ReportRecords.report_id == report_id)
                .values(
                    {"report_status": report_status, "exception": exception, "update_time": datetime.now(timezone.utc)}
                )
            )
            session.execute(stmt)
            session.commit()
        finally:
            session.close()

    async def _get_next_nonce(self):
        online_nonce = await self.event_loop.run_in_executor(
            self.thread_pool,
            self.web3.eth.get_transaction_count,
            self.account.address,
        )
        if self.nonce == online_nonce:
            self.nonce -= 1
        current_nonce = max(self.nonce, online_nonce)
        self.nonce = current_nonce + 1 if current_nonce == online_nonce else self.nonce
        return current_nonce

    async def _process_transaction(self, info: dict) -> bool:
        txn_hash, report_id = None, None
        builder = info["transaction_builder"]
        parameters = info["transaction_parameters"]
        report_from = info["report_from"]

        self.logger.info(f"Processing transaction with parameters: {parameters}")

        for entire_retry in range(self.max_retries):
            for submit_retry in range(self.max_retries):
                async with self.nonce_lock:
                    try:
                        parameters["nonce"] = await self._get_next_nonce()

                        signed_txn = builder(**parameters)
                        txn_hash = await self.event_loop.run_in_executor(
                            self.thread_pool, self.web3.eth.send_raw_transaction, signed_txn.rawTransaction
                        )

                        self.logger.info(
                            f"Submitted transaction {signed_txn} successfully with parameter: {parameters}.\n"
                            f"Waiting for receipt."
                        )

                        report_id = await self.submit_record_to_db(
                            parameters, transaction_hash=txn_hash, report_from=report_from
                        )
                        break

                    except ValueError as e:
                        if (
                            str(e).find("nonce too low") != -1
                            or str(e).find("replacement transaction underpriced") != -1
                        ):
                            self.logger.error(e)
                            self.logger.warning(
                                "Reporter will retry to submit the transaction with another nonce. "
                                f"Now nonce: {self.nonce}"
                            )
                            async with self.nonce_lock:
                                self.nonce += 1

                    except Exception as e:
                        self.logger.error(
                            f"Building and submitting transaction failed with parameter: {parameters}. {e}"
                        )
                        await asyncio.sleep(self.retry_delay)

            receipt = await self._wait_for_receipt(txn_hash)
            if receipt is None:
                self.logger.warning(
                    f"Transaction: {bytes_to_hex_str(txn_hash)} had not been receipted by chain. \n"
                    f"Reporter will retry to submit the transaction with info: {parameters}. \n "
                )
                await self.update_report_status(
                    report_id,
                    ReportStatus.NO_RECEIPT,
                    exception=f"Transaction is not in the chain after "
                    f"{self.receipt_timeout * self.max_retries} seconds.",
                )
            elif receipt["status"] == 1:
                self.logger.info(f"Transaction {bytes_to_hex_str(txn_hash)} had been receipted.")
                await self.update_report_status(report_id, ReportStatus.SUCCESS)
                return True
            elif receipt["status"] == 0:
                self.logger.warning(
                    f"Transaction: {bytes_to_hex_str(txn_hash)} failed. \n"
                    f"with info: {parameters}\n"
                    f"Receipt: {receipt}\n"
                    f"Reporter will retry to submit the transaction with info: {parameters}. \n "
                )
                await self.update_report_status(report_id, ReportStatus.TRANSACTION_FAILED)

            await asyncio.sleep(self.retry_delay)

        return False

    async def _wait_for_receipt(self, txn_hash):
        receipt = None
        for receipt_retry in range(self.max_retries):
            try:
                receipt = await self.event_loop.run_in_executor(
                    self.thread_pool,
                    lambda: self.web3.eth.wait_for_transaction_receipt(
                        txn_hash, timeout=self.receipt_timeout, poll_latency=self.receipt_poll_latency
                    ),
                )
            except TimeExhausted as e:
                self.logger.warning(
                    f"Transaction: {bytes_to_hex_str(txn_hash)} is not in the chain after "
                    f"{self.receipt_timeout * (receipt_retry + 1)} seconds. \n"
                    f"Reporter will continue to retry waiting for receipt "
                    f"{self.max_retries - receipt_retry - 1} times, {self.receipt_timeout} seconds each time.\n"
                )

        return receipt


class RecordReporter:

    def __init__(self, private_key, from_address, service):
        self.web3 = Web3(Web3.HTTPProvider(REQUEST_RPC))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.from_address = from_address
        self.contract = self.web3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=[SUBMIT_INDEX_FUNCTION.get_abi()],
        )
        self.transaction_submitter = AsyncTransactionSubmitter(web3=self.web3, account=self.account, service=service)
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)

        self.start()

    def start(self):
        self.transaction_submitter.start()

    def stop(self):
        self.transaction_submitter.stop()

    def report(
        self,
        chain_id: int,
        start_block: int,
        end_block: int,
        runtime_code_hash: str,
        indexed_data: dict,
        report_from: str,
    ):
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
                "report_from": report_from,
            }
        )


class FeatureRegister:
    def __init__(self, private_key, from_address):
        self.web3 = Web3(Web3.HTTPProvider(REQUEST_RPC))
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.from_address = from_address
        self.contract = self.web3.eth.contract(
            address=CONTRACT_ADDRESS,
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
