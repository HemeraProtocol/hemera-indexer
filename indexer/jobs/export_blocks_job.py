import json
import logging

from enumeration.entity_type import EntityType
from indexer.domain.block import Block
from indexer.domain.block_ts_mapper import BlockTsMapper
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from indexer.utils.utils import rpc_response_batch_to_results

logger = logging.getLogger(__name__)


# Exports blocks and block number <-> timestamp mapping
class ExportBlocksJob(BaseJob):
    dependency_types = []
    output_types = [Block]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_web3_provider = kwargs['batch_web3_provider']
        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__)
        self._is_batch = kwargs['batch_size'] > 1
        self._item_exporters = kwargs['item_exporters']

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):

        self._start_block = int(kwargs['start_block'])
        self._end_block = int(kwargs['end_block'])

        self._batch_work_executor.execute(
            range(self._start_block, self._end_block + 1),
            self._collect_batch,
            total_items=self._end_block - self._start_block + 1
        )
        self._batch_work_executor.shutdown()

    def _collect_batch(self, block_number_batch):
        results = blocks_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)
        for block_rpc_dict in results:
            block_entity = Block(block_rpc_dict)
            self._collect_item(Block.type(), block_entity)
            for transaction_entity in block_entity.transactions:
                self._collect_item(Transaction.type(), transaction_entity)

    def _process(self):
        self._data_buff[Block.type()].sort(key=lambda x: x.number)
        self._data_buff[Transaction.type()].sort(key=lambda x: (x.block_number, x.transaction_index))

        ts_dict = {}
        for block in self._data_buff[Block.type()]:
            timestamp = block.timestamp // 3600 * 3600
            block_number = block.number

            if timestamp not in ts_dict or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number

        self._data_buff[BlockTsMapper.type()] = [BlockTsMapper((ts, block)) for ts, block in ts_dict.items()]

    def _export(self):
        items = []
        if self._entity_types & EntityType.BLOCK:
            items = self._extract_from_buff([Block.type()])
        for item_exporter in self._item_exporters:
            item_exporter.open()
            item_exporter.export_items(items)
            item_exporter.close()


def blocks_rpc_requests(make_request, block_number_batch, is_batch):
    block_number_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))

    if is_batch:
        response = make_request(params=json.dumps(block_number_rpc))
    else:
        response = [make_request(params=json.dumps(block_number_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
