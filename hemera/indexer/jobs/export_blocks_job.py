import logging

import orjson

from hemera.common.utils.exception_control import FastShutdownError
from hemera.indexer.domains.block import Block
from hemera.indexer.domains.block_ts_mapper import BlockTsMapper
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseExportJob
from hemera.indexer.specification.specification import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    TransactionFilterByLogs,
    TransactionFilterByTransactionInfo,
    TransactionHashSpecification,
)
from hemera.indexer.utils.collection_utils import distinct_collections_by_group, flatten
from hemera.indexer.utils.json_rpc_requests import generate_get_block_by_number_json_rpc
from hemera.indexer.utils.reorg import set_reorg_sign
from hemera.indexer.utils.rpc_utils import rpc_response_batch_to_results

logger = logging.getLogger(__name__)


# Exports blocks and block number <-> timestamp mapping
class ExportBlocksJob(BaseExportJob):
    dependency_types = []
    output_types = [Block, BlockTsMapper]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = flatten(kwargs.get("filters", []))
        self._is_filter = kwargs.get("is_filter", False)
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()
        self._reorg_jobs = kwargs.get("reorg_jobs", [])

    def _pre_reorg(self, **kwargs):
        if self._service is None:
            raise FastShutdownError("PG Service is not set")

        reorg_block = int(kwargs["start_block"])
        set_reorg_sign(self._reorg_jobs, reorg_block, self._service)
        self._should_reorg_type.add(Block.type())
        self._should_reorg = True

    def _end(self):
        super()._end()
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

    def _collect(self, **kwargs):

        self._start_block = int(kwargs["start_block"])
        self._end_block = int(kwargs["end_block"])

        blocks = range(self._start_block, self._end_block + 1)
        total_items = len(blocks)

        is_only_log_filter = True
        filter_blocks = set()
        if self._is_filter:
            for filter in self._filters:
                if isinstance(filter, TransactionFilterByLogs):
                    for filter_param in filter.get_eth_log_filters_params():
                        filter_param.update({"fromBlock": self._start_block, "toBlock": self._end_block})
                        logs = self._web3.eth.get_logs(filter_param)
                        filter_blocks.update(set([log["blockNumber"] for log in logs]))
                        transaction_hashes = set([log["transactionHash"] for log in logs])
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

        self._batch_work_executor.execute(blocks, self._collect_batch, total_items=total_items)
        self._batch_work_executor.wait()

    def _collect_batch(self, block_number_batch):
        results = blocks_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)
        for block_rpc_dict in results:
            block_entity = Block.from_rpc(block_rpc_dict)
            self._collect_item(Block.type(), block_entity)

            satisfied_transactions = []
            for transaction_entity in block_entity.transactions:
                if self._specification.is_satisfied_by(transaction_entity):
                    satisfied_transactions.append(transaction_entity)
            block_entity.transactions = satisfied_transactions

    def _process(self, **kwargs):
        self._data_buff[Block.type()] = distinct_collections_by_group(self._data_buff[Block.type()], ["hash"])
        self._data_buff[Block.type()].sort(key=lambda x: x.number)

        ts_dict = {}
        for block in self._data_buff[Block.type()]:
            timestamp = block.timestamp // 3600 * 3600
            block_number = block.number

            if timestamp not in ts_dict or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number

        self._collect_items(BlockTsMapper.type(), [BlockTsMapper((ts, block)) for ts, block in ts_dict.items()])


def blocks_rpc_requests(make_request, block_number_batch, is_batch):
    block_number_rpc = list(generate_get_block_by_number_json_rpc(block_number_batch, True))

    if is_batch:
        response = make_request(params=orjson.dumps(block_number_rpc))
    else:
        response = [make_request(params=orjson.dumps(block_number_rpc[0]))]

    results = rpc_response_batch_to_results(response)
    return results
