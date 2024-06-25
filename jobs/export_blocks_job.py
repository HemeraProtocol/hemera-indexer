import json

from domain.block import format_block_data
from domain.block_ts_mapper import format_block_ts_mapper
from enumeration.entity_type import EntityType
from executors.batch_work_executor import BatchWorkExecutor
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from utils.utils import rpc_response_batch_to_results, validate_range


# Exports blocks and block number <-> timestamp mapping
class ExportBlocksJob(BaseJob):
    def __init__(self,
                 index_keys,
                 entity_types,
                 start_block,
                 end_block,
                 batch_web3_provider,
                 batch_size,
                 max_workers,
                 item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)
        validate_range(start_block, end_block)
        self._start_block = start_block
        self._end_block = end_block
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(
            range(self._start_block, self._end_block + 1),
            self._collect_batch,
            total_items=self._end_block - self._start_block + 1
        )
        self._batch_work_executor.shutdown()

    def _collect_batch(self, block_number_batch):
        results = blocks_rpc_requests(self._batch_web3_provider.make_batch_request, block_number_batch)

        for block in results:
            block['item'] = 'block'
            self._collect_item(block)
            for transaction in block['transactions']:
                transaction['item'] = 'transaction'
                self._collect_item(transaction)

    def _process(self):
        self._data_buff['formated_block'] = [format_block_data(block) for block in self._data_buff['block']]
        self._data_buff['formated_block'] = sorted(self._data_buff['formated_block'], key=lambda x: x['number'])

        ts_dict = {}
        for block in self._data_buff['formated_block']:
            timestamp = int(block['timestamp'] / 3600) * 3600
            block_number = block['number']

            if timestamp not in ts_dict.keys() or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number
        self._data_buff['block_ts_mapping'] = []
        for timestamp, block_number in ts_dict.items():
            self._data_buff['block_ts_mapping'].append(format_block_ts_mapper(timestamp, block_number))

    def _export(self):
        export_items = self._extract_from_buff(['block_ts_mapping'])

        if self._entity_types & EntityType.BLOCK:
            export_items.extend(self._extract_from_buff(['formated_block']))

        self._item_exporter.export_items(export_items)


def blocks_rpc_requests(make_request, block_number_batch):
    block_number_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))
    response = make_request(json.dumps(block_number_rpc))
    results = rpc_response_batch_to_results(response)

    return results
