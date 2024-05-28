import json

from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_trace_block_by_number_json_rpc
from jobs.base_job import BaseJob
from utils.utils import validate_range, rpc_response_to_result


# Exports geth traces
class ExportGethTracesJob(BaseJob):
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
        trace_block_rpc = list(generate_trace_block_by_number_json_rpc(block_number_batch))
        response = self.batch_web3_provider.make_batch_request(json.dumps(trace_block_rpc))

        for response_item in response:
            block_number = response_item.get('id')
            result = rpc_response_to_result(response_item)

            geth_trace = {
                'item': 'geth_trace',
                'block_number': block_number,
                'transaction_traces': result,
            }

            self._export_item(geth_trace)

    def _end(self):
        self.batch_work_executor.shutdown()
