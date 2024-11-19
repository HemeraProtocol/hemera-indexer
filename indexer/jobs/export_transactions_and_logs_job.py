import logging
from typing import List

import orjson

from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.receipt import Receipt
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.utils.json_rpc_requests import generate_get_receipt_json_rpc
from indexer.utils.rpc_utils import rpc_response_batch_to_results


# Exports transactions and logs
class ExportTransactionsAndLogsJob(BaseExportJob):
    dependency_types = [Block]
    output_types = [Transaction, Log]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _start(self, **kwargs):
        super()._start(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            self._batch_size,
            self._max_workers,
            job_name=self.__class__.__name__,
        )

    def _collect(self, **kwargs):

        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])

        self._batch_work_executor.execute(transactions, self._collect_batch, total_items=len(transactions))
        self._batch_work_executor.wait()

    def _collect_batch(self, transactions: List[Transaction]):
        transaction_hash_mapper = {transaction.hash: transaction for transaction in transactions}
        results = receipt_rpc_requests(
            self._batch_web3_provider.make_request,
            transaction_hash_mapper.keys(),
            self._is_batch,
        )

        for receipt in results:
            transaction = transaction_hash_mapper[receipt["transactionHash"]]
            receipt_entity = Receipt.from_rpc(
                receipt,
                transaction.block_timestamp,
                transaction.block_hash,
                transaction.block_number,
            )
            transaction.fill_with_receipt(receipt_entity)

            for log in transaction.receipt.logs:
                self._collect_item(Log.type(), log)

    def _process(self, **kwargs):
        self._data_buff[Log.type()].sort(key=lambda x: (x.block_number, x.log_index))


def receipt_rpc_requests(make_request, transaction_hashes, is_batch):
    receipts_rpc = list(generate_get_receipt_json_rpc(transaction_hashes))

    if is_batch:
        response = make_request(params=orjson.dumps(receipts_rpc))
    else:
        response = [make_request(params=orjson.dumps(receipts_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
