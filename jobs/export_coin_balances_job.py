import json

from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_balance_json_rpc
from utils.utils import rpc_response_to_result
from domain.trace import trace_is_contract_creation, trace_is_transfer_value


# Exports coin balance
class ExportCoinBalancesJob(BaseJob):
    def __init__(
            self,
            blocks_iterable,
            transactions_iterable,
            traces_iterable,
            batch_size,
            batch_web3_provider,
            max_workers,
            index_keys):

        self.blocks_iterable = blocks_iterable
        self.transactions_iterable = transactions_iterable
        self.traces_iterable = traces_iterable

        coin_addresses = set()
        blocks_timestamp_dict = dict()
        for block in self.blocks_iterable:
            coin_addresses.add((block['miner'], block['number'], block['timestamp']))
            blocks_timestamp_dict[block['number']] = block['timestamp']

        for transaction in self.transactions_iterable:
            block_timestamp = blocks_timestamp_dict[transaction['blockNumber']]
            if transaction['to'] is not None:
                coin_addresses.add((transaction['to'], transaction['blockNumber'], block_timestamp))
            if transaction['from'] is not None:
                coin_addresses.add((transaction['from'], transaction['blockNumber'], block_timestamp))

        for trace in self.traces_iterable:
            block_number = hex(trace['block_number'])
            if trace_is_contract_creation(trace) or trace_is_transfer_value(trace):
                if trace['to_address'] is not None:
                    coin_addresses.add(
                        (trace['to_address'], block_number, blocks_timestamp_dict[block_number]))
                if trace['from_address'] is not None:
                    coin_addresses.add(
                        (trace['from_address'], block_number, blocks_timestamp_dict[block_number]))

        self.coin_addresses = []
        for address in list(coin_addresses):
            self.coin_addresses.append({
                'address': address[0],
                'block_number': address[1],
                'block_timestamp': address[2]
            })

        self.batch_web3_provider = batch_web3_provider

        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.coin_addresses, self._export_batch)

    def _export_batch(self, coin_addresses):
        coin_balance_rpc = list(generate_get_balance_json_rpc(coin_addresses))
        response = self.batch_web3_provider.make_batch_request(json.dumps(coin_balance_rpc))

        for data in list(zip(response, coin_addresses)):
            result = rpc_response_to_result(data[0])

            coin_balance = {
                'item': 'coin_balance',
                'address': data[1]['address'],
                'balance': int(result, 16),
                'block_number': data[1]['block_number'],
                'block_timestamp': data[1]['block_timestamp'],
            }

            self._export_item(coin_balance)

    def _end(self):
        self.batch_work_executor.shutdown()
