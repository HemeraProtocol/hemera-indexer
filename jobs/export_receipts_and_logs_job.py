import json

from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_receipt_json_rpc
from utils.utils import rpc_response_batch_to_results


# Exports receipts and logs
class ExportReceiptsAndLogsJob(BaseJob):
    def __init__(
            self,
            transactions,
            batch_size,
            batch_web3_provider,
            max_workers,
            index_keys):
        self.batch_web3_provider = batch_web3_provider
        self.transactions = transactions
        self.transaction_hashes_iterable = (transaction['hash'] for transaction in transactions)

        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.transaction_hashes_iterable, self._export_receipts)

    def _export_receipts(self, transaction_hashes):
        receipts_rpc = list(generate_get_receipt_json_rpc(transaction_hashes))
        response = self.batch_web3_provider.make_batch_request(json.dumps(receipts_rpc))
        results = rpc_response_batch_to_results(response)
        receipts = [result for result in results]
        for receipt in receipts:
            receipt['item'] = 'receipt'
            self._export_receipt(receipt)

    def _export_receipt(self, receipt):
        self._export_item(receipt)
        for log in receipt['logs']:
            log['item'] = 'log'
            self._export_item(log)

    def _end(self):
        self.batch_work_executor.shutdown()
