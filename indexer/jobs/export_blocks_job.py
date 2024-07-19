import json
import logging

from indexer.domain.block import Block
from indexer.domain.block_ts_mapper import BlockTsMapper
from enumeration.entity_type import EntityType
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from indexer.utils.utils import rpc_response_batch_to_results, validate_range

logger = logging.getLogger(__name__)


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
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
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
        results = blocks_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)

        for block in results:
            block_entity = Block(block)
            self._collect_item('origin_block', block)
            self._collect_item('block', block_entity)
            for transaction in block['transactions']:
                self._collect_item('origin_transaction', transaction)
            for transaction in block_entity.transactions:
                self._collect_item('transaction', transaction)

    def _process(self):
        self._data_buff['block'] = sorted(self._data_buff['block'], key=lambda x: x.number)
        self._data_buff['transaction'] = sorted(self._data_buff['transaction'],
                                                key=lambda x: (x.block_number, x.transaction_index))

        ts_dict = {}
        for block in self._data_buff['block']:
            timestamp = block.timestamp // 3600 * 3600
            block_number = block.number

            if timestamp not in ts_dict or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number

        self._data_buff['block_ts_mapper'] = [BlockTsMapper((ts, block)) for ts, block in ts_dict.items()]

    def _export(self):
        export_items = self._extract_from_buff(['block_ts_mapper'])

        if self._entity_types & EntityType.BLOCK:
            export_items.extend(self._extract_from_buff(['block']))

        self._item_exporter.export_items(export_items)


def blocks_rpc_requests(make_request, block_number_batch, is_batch):
    block_number_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))

    if is_batch:
        response = make_request(params=json.dumps(block_number_rpc))
    else:
        response = [make_request(params=json.dumps(block_number_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
