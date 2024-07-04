import json
import logging

from domain.log import format_log_data
from domain.transaction import format_transaction_data
from enumeration.entity_type import EntityType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.enrich import enrich_blocks_timestamp, enrich_transactions
from utils.json_rpc_requests import generate_get_receipt_json_rpc
from utils.utils import rpc_response_batch_to_results

logger = logging.getLogger(__name__)


# Exports transactions and logs
class ExportTransactionsAndLogsJob(BaseJob):
    def __init__(self,
                 index_keys,
                 entity_types,
                 batch_web3_provider,
                 batch_size,
                 max_workers,
                 item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        transaction_hashes_iterable = [transaction['hash'] for transaction in self._data_buff['transaction']]
        self._batch_work_executor.execute(transaction_hashes_iterable,
                                          self._collect_batch,
                                          total_items=len(transaction_hashes_iterable))
        self._batch_work_executor.shutdown()

    def _collect_batch(self, transaction_hashes):
        results = receipt_rpc_requests(self._batch_web3_provider.make_request, transaction_hashes, self._is_batch)

        for receipt in results:
            receipt['item'] = 'receipt'
            self._collect_item(receipt)
            for log in receipt['logs']:
                log['item'] = 'log'
                self._collect_item(log)

    def _process(self):
        self._data_buff['enriched_transaction'] = [format_transaction_data(transaction)
                                                   for transaction in enrich_blocks_timestamp
                                                   (self._data_buff['formated_block'],
                                                    enrich_transactions(self._data_buff['transaction'],
                                                                        self._data_buff['receipt']))]

        self._data_buff['enriched_log'] = [format_log_data(log) for log in
                                           enrich_blocks_timestamp(self._data_buff['formated_block'],
                                                                   self._data_buff['log'])]

        self._data_buff['enriched_transaction'] = sorted(self._data_buff['enriched_transaction'],
                                                         key=lambda x: (x['block_number'],
                                                                        x['transaction_index']))

        self._data_buff['enriched_log'] = sorted(self._data_buff['enriched_log'],
                                                 key=lambda x: (x['block_number'],
                                                                x['transaction_index'],
                                                                x['log_index']))

    def _export(self):
        items = []
        if self._entity_types & EntityType.TRANSACTION:
            items.extend(self._extract_from_buff(['enriched_transaction']))

        if self._entity_types & EntityType.LOG:
            items.extend(self._extract_from_buff(['enriched_log']))

        self._item_exporter.export_items(items)


def receipt_rpc_requests(make_request, transaction_hashes, is_batch):
    receipts_rpc = list(generate_get_receipt_json_rpc(transaction_hashes))

    if is_batch:
        response = make_request(params=json.dumps(receipts_rpc))
    else:
        response = [make_request(params=json.dumps(receipts_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
