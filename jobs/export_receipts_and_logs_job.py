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
            item_exporter,
            export_receipts=True,
            export_logs=True):
        self.batch_web3_provider = batch_web3_provider
        self.transactions = transactions
        self.transaction_hashes_iterable = (transaction['hash'] for transaction in transactions)

        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.item_exporter = item_exporter

        self.export_receipts = export_receipts
        self.export_logs = export_logs
        if not self.export_receipts and not self.export_logs:
            raise ValueError('At least one of export_receipts or export_logs must be True')


    def _start(self):
        self.item_exporter.open()

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
        if self.export_receipts:
            self.item_exporter.export_item(receipt)
        if self.export_logs:
            for log in receipt['logs']:
                log['item'] = 'log'
                self.item_exporter.export_item(log)

    def _end(self):
        self.batch_work_executor.shutdown()
        self.item_exporter.close()
