import json

import pandas

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

        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):

        coin_addresses = distinct_addresses(self._data_buff['formated_block'],
                                            self._data_buff['enriched_transaction'],
                                            self._data_buff['enriched_traces'])
        self._batch_work_executor.execute(coin_addresses, self._collect_batch)
        self._batch_work_executor.shutdown()

    def _collect_batch(self, coin_addresses):
        coin_balances = coin_balances_rpc_requests(self._batch_web3_provider.make_request,
                                                   coin_addresses,
                                                   self._is_batch)

        for coin_balance in coin_balances:
            coin_balance['item'] = 'coin_balance'
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


def distinct_addresses(blocks, transactions, traces):
    addresses = []
    for block in blocks:
        addresses.append({
            'address': block['miner'],
            'block_number': block['number'],
            'block_timestamp': block['timestamp']
        })

    for transaction in transactions:
        if transaction['from_address'] is not None:
            addresses.append({
                'address': transaction['from_address'],
                'block_number': transaction['block_number'],
                'block_timestamp': transaction['block_timestamp']
            })

        if transaction['to_address'] is not None:
            addresses.append({
                'address': transaction['to_address'],
                'block_number': transaction['block_number'],
                'block_timestamp': transaction['block_timestamp']
            })

    for trace in traces:
        if trace_is_contract_creation(trace) or trace_is_transfer_value(trace, True):
            if trace['to_address'] is not None:
                addresses.append({
                    'address': trace['to_address'],
                    'block_number': trace['block_number'],
                    'block_timestamp': trace['block_timestamp']
                })
            if trace['from_address'] is not None:
                addresses.append({
                    'address': trace['from_address'],
                    'block_number': trace['block_number'],
                    'block_timestamp': trace['block_timestamp']
                })

    return pandas.DataFrame(addresses).drop_duplicates().to_dict(orient='records')


def coin_balances_rpc_requests(make_requests, addresses, is_batch):
    coin_balance_rpc = list(generate_get_balance_json_rpc(addresses))

    if is_batch:
        response = make_requests(params=json.dumps(coin_balance_rpc))
    else:
        response = [make_requests(params=json.dumps(coin_balance_rpc[0]))]

    coin_balances = []
    for data in list(zip(response, addresses)):
        result = rpc_response_to_result(data[0])

        coin_balances.append({
            'address': data[1]['address'],
            'balance': int(result, 16),
            'block_number': data[1]['block_number'],
            'block_timestamp': data[1]['block_timestamp'],
        })

    return coin_balances
