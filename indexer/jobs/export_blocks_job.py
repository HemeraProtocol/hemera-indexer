import json
import logging

from web3 import Web3

from enumeration.entity_type import EntityType
from indexer.domain.block import Block
from indexer.domain.block_ts_mapper import BlockTsMapper
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.specification.specification import TransactionFilterByLogs, \
    AlwaysFalseSpecification, TransactionFilterByTransactionInfo, TransactionHashSpecification, AlwaysTrueSpecification
from indexer.utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from indexer.utils.utils import rpc_response_batch_to_results

logger = logging.getLogger(__name__)


# Exports blocks and block number <-> timestamp mapping
class ExportBlocksJob(BaseJob):
    dependency_types = []
    output_types = [Block]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__)
        self._is_batch = kwargs['batch_size'] > 1
        self._filters = kwargs.get('filters', None)
        self._is_filter = self._filters is not None and len(self._filters) > 0
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):

        self._start_block = int(kwargs['start_block'])
        self._end_block = int(kwargs['end_block'])

        blocks = range(self._start_block, self._end_block + 1)
        total_items = len(blocks)

        is_only_log_filter = True
        filter_blocks = set()
        if EntityType.entity_filter_mode(self._entity_types):
            for filter in self._filters:
                if isinstance(filter, TransactionFilterByLogs):
                    filter_params = filter.get_eth_log_filters_params()
                    filter_params.update({'fromBlock': self._start_block, 'toBlock': self._end_block})
                    logs = self._web3.eth.get_logs(filter_params)
                    filter_blocks.update(set([log['blockNumber'] for log in logs]))
                    transaction_hashes = set([log['transactionHash'] for log in logs])
                    transaction_hashes = [h.hex() for h in transaction_hashes]
                    self._specification |= TransactionHashSpecification(transaction_hashes)
                elif isinstance(filter, TransactionFilterByTransactionInfo):
                    is_only_log_filter = False
                    self._specification |= filter.get_or_specification()
                else:
                    raise ValueError(f"Unsupported filter type: {type(filter)}")
        if self._is_filter and is_only_log_filter:
            blocks = list(filter_blocks)
            total_items = len(blocks)

        self._batch_work_executor.execute(
            blocks,
            self._collect_batch,
            total_items=total_items
        )
        self._batch_work_executor.shutdown()

    def _collect_batch(self, block_number_batch):
        results = blocks_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)
        for block_rpc_dict in results:
            block_entity = Block.from_rpc(block_rpc_dict)
            self._collect_item(Block.type(), block_entity)
            for transaction_entity in block_entity.transactions:
                if self._specification.is_satisfied_by(transaction_entity):
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
        self._item_exporter.open()
        self._item_exporter.export_items(items)
        self._item_exporter.close()


def blocks_rpc_requests(make_request, block_number_batch, is_batch):
    block_number_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))

    if is_batch:
        response = make_request(params=json.dumps(block_number_rpc))
    else:
        response = [make_request(params=json.dumps(block_number_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
