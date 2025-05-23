import logging
from typing import List, Union

import orjson

from hemera.indexer.domains.block import Block
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.receipt import Receipt
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseExportJob, Collector
from hemera.indexer.utils.collection_utils import flatten
from hemera.indexer.utils.json_rpc_requests import (
    generate_get_receipt_from_blocks_json_rpc,
    generate_get_receipt_json_rpc,
)
from hemera.indexer.utils.rpc_utils import rpc_response_batch_to_results, zip_rpc_response

logger = logging.getLogger(__name__)


# Exports transactions and logs
class ExportTransactionsAndLogsJob(BaseExportJob):
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._use_receipt_from_blocks_rpc = self.user_defined_config.get("use_receipt_from_blocks_rpc") or False

    def request_for_receipt_from_block(self, blocks: List[Block], output: Collector):
        transaction_hash_mapper = {
            transaction.hash: transaction for block in blocks for transaction in block.transactions
        }
        results = receipt_rpc_from_block_number_requests(
            self._batch_web3_provider.make_request,
            [block.number for block in blocks],
            self._is_batch,
        )
        for block, receipts in zip_rpc_response(blocks, results, index="number"):
            for receipt in receipts:
                transaction = transaction_hash_mapper[receipt["transactionHash"]]
                receipt_entity = Receipt.from_rpc(
                    receipt,
                    block.timestamp,
                    block.hash,
                    block.number,
                )
                transaction.fill_with_receipt(receipt_entity)

                for log in transaction.receipt.logs:
                    output.collect(log)

    def request_for_receipt(self, blocks: List[Block], output: Collector):
        transaction_hash_mapper = {
            transaction.hash: transaction for block in blocks for transaction in block.transactions
        }

        if self._use_receipt_from_blocks_rpc:
            results = receipt_rpc_from_block_number_requests(
                self._batch_web3_provider.make_request,
                [block.number for block in blocks],
                self._is_batch,
            )
        else:
            results = receipt_rpc_requests(
                self._batch_web3_provider.make_request,
                transaction_hash_mapper.keys(),
                self._is_batch,
            )

        for receipt in results:
            if receipt is None:
                continue
            transaction = transaction_hash_mapper.get(receipt["transactionHash"])
            if transaction:
                receipt_entity = Receipt.from_rpc(
                    receipt,
                    transaction.block_timestamp,
                    transaction.block_hash,
                    transaction.block_number,
                )
                transaction.fill_with_receipt(receipt_entity)
                output.collect(transaction)

                for log in transaction.receipt.logs:
                    output.collect(log)

    def _udf(self, blocks: List[Block], output: Collector[Union[Transaction, Log]]):
        self._batch_work_executor.execute(blocks, self.request_for_receipt, collector=output, total_items=len(blocks))
        self._batch_work_executor.wait()

        self._data_buff[Transaction.type()].sort(key=lambda x: (x.block_number, x.transaction_index))
        self._data_buff[Log.type()].sort(key=lambda x: (x.block_number, x.log_index))


def receipt_rpc_requests(make_request, transaction_hashes, is_batch):
    receipts_rpc = list(generate_get_receipt_json_rpc(transaction_hashes))

    if is_batch:
        response = make_request(params=orjson.dumps(receipts_rpc))
    else:
        response = [make_request(params=orjson.dumps(receipts_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return list(results)


def receipt_rpc_from_block_number_requests(make_request, block_numbers, is_batch):
    receipts_rpc = list(generate_get_receipt_from_blocks_json_rpc(block_numbers))

    if is_batch:
        response = make_request(params=orjson.dumps(receipts_rpc))
    else:
        response = [make_request(params=orjson.dumps(receipts_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return flatten(results)
