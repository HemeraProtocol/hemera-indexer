import json

from executors.batch_work_executor import BatchWorkExecutor
from jobs.base_job import BaseJob
from utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from utils.utils import rpc_response_batch_to_results, validate_range


# Exports blocks and transactions
class ExportBlocksAndTransactionsJob(BaseJob):
    def __init__(
            self,
            start_block,
            end_block,
            batch_size,
            batch_web3_provider,
            max_workers,
            index_keys):
        validate_range(start_block, end_block)
        self.start_block = start_block
        self.end_block = end_block
        self.batch_web3_provider = batch_web3_provider
        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(
            range(self.start_block, self.end_block + 1),
            self._export_batch,
            total_items=self.end_block - self.start_block + 1
        )

    def _export_batch(self, block_number_batch):
        blocks_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))
        response = self.batch_web3_provider.make_batch_request(json.dumps(blocks_rpc))
        results = rpc_response_batch_to_results(response)

        for block in results:
            block['item'] = 'block'
            self._export_item(block)
            self._export_transaction(block)

    def _export_transaction(self, block):
        for transaction in block['transactions']:
            transaction['item'] = 'transaction'
            self._export_item(transaction)

    def _end(self):
        self.batch_work_executor.shutdown()
