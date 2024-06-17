import json

from domain.coin_balance import format_coin_balance_data
from enumeration.entity_type import EntityType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_balance_json_rpc
from utils.utils import rpc_response_to_result
from domain.trace import trace_is_contract_creation, trace_is_transfer_value
from utils.web3_utils import verify_0_address


# Exports coin balances
class ExportCoinBalancesJob(BaseJob):
    def __init__(
            self,
            index_keys,
            entity_types,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        coin_addresses = set()
        blocks_timestamp_dict = dict()
        for block in self._data_buff['block']:
            coin_addresses.add((block['miner'], block['number'], block['timestamp']))
            blocks_timestamp_dict[block['number']] = block['timestamp']

        for transaction in self._data_buff['transaction']:
            block_timestamp = blocks_timestamp_dict[transaction['blockNumber']]
            if transaction['to'] is not None:
                coin_addresses.add((transaction['to'], transaction['blockNumber'], block_timestamp))
            if transaction['from'] is not None:
                coin_addresses.add((transaction['from'], transaction['blockNumber'], block_timestamp))

        for trace in self._data_buff['trace']:
            block_number = hex(trace['block_number'])
            if trace_is_contract_creation(trace) or trace_is_transfer_value(trace):
                if trace['to_address'] is not None:
                    coin_addresses.add(
                        (trace['to_address'], block_number, blocks_timestamp_dict[block_number]))
                if trace['from_address'] is not None:
                    coin_addresses.add(
                        (trace['from_address'], block_number, blocks_timestamp_dict[block_number]))

        self._coin_addresses = []
        for address in list(coin_addresses):
            if not verify_0_address(address[0]):
                self._coin_addresses.append({
                    'address': address[0],
                    'block_number': address[1],
                    'block_timestamp': address[2]
                })

        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(self._coin_addresses, self._collect_batch)

    def _collect_batch(self, coin_addresses):
        coin_balance_rpc = list(generate_get_balance_json_rpc(coin_addresses))
        response = self._batch_web3_provider.make_batch_request(json.dumps(coin_balance_rpc))

        for data in list(zip(response, coin_addresses)):
            result = rpc_response_to_result(data[0])

            coin_balance = {
                'item': 'coin_balance',
                'address': data[1]['address'],
                'balance': int(result, 16),
                'block_number': data[1]['block_number'],
                'block_timestamp': data[1]['block_timestamp'],
            }

            self._collect_item(coin_balance)

    def _process(self):

        self._data_buff['formated_coin_balance'] = [format_coin_balance_data(coin_balance) for coin_balance in
                                                    self._data_buff['coin_balance']]

        self._data_buff['formated_coin_balance'] = sorted(self._data_buff['formated_coin_balance'],
                                                          key=lambda x: (x['block_number'], x['address']))

    def _export(self):
        if self._entity_types & EntityType.COIN_BALANCE:
            items = self._extract_from_buff(['formated_coin_balance'])
            self._item_exporter.export_items(items)

    def _end(self):
        self._batch_work_executor.shutdown()
        super()._end()
