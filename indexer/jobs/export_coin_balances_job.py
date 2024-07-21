import json
import logging
from typing import List

import pandas
from eth_utils import to_int

from indexer.domain.block import Block
from indexer.domain.coin_balance import CoinBalance
from enumeration.entity_type import EntityType
from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.utils.json_rpc_requests import generate_get_balance_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)


# Exports coin balances
class ExportCoinBalancesJob(BaseJob):
    def __init__(
            self,
            entity_types,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(entity_types=entity_types)

        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):

        coin_addresses = distinct_addresses(self._data_buff[Block.type()],
                                            self._data_buff[Transaction.type()],
                                            self._data_buff[Trace.type()])
        self._batch_work_executor.execute(coin_addresses, self._collect_batch, total_items=len(coin_addresses))
        self._batch_work_executor.shutdown()

    def _collect_batch(self, coin_addresses):
        coin_balances = coin_balances_rpc_requests(self._batch_web3_provider.make_request,
                                                   coin_addresses,
                                                   self._is_batch)

        for coin_balance in coin_balances:
            self._collect_item(CoinBalance.type(), CoinBalance(coin_balance))

    def _process(self):

        self._data_buff[CoinBalance.type()].sort(
            key=lambda x: (x.block_number, x.address))

    def _export(self):
        if self._entity_types & EntityType.COIN_BALANCE:
            items = self._extract_from_buff(['formated_coin_balance'])
            self._item_exporter.export_items(items)


def distinct_addresses(blocks: List[Block], transactions: List[Transaction], traces: List[Trace]):
    addresses = []
    for block in blocks:
        addresses.append({
            'address': block.miner,
            'block_number': block.number,
            'block_timestamp': block.timestamp
        })

    for transaction in transactions:
        if transaction.from_address is not None:
            addresses.append({
                'address': transaction.from_address,
                'block_number': transaction.block_number,
                'block_timestamp': transaction.block_timestamp
            })

        if transaction.to_address is not None:
            addresses.append({
                'address': transaction.to_address,
                'block_number': transaction.block_number,
                'block_timestamp': transaction.block_timestamp
            })

    for trace in traces:
        if trace.is_contract_creation() or trace.is_transfer_value():
            if trace.to_address is not None:
                addresses.append({
                    'address': trace.to_address,
                    'block_number': trace.block_number,
                    'block_timestamp': trace.block_timestamp
                })
            if trace.from_address is not None:
                addresses.append({
                    'address': trace.from_address,
                    'block_number': trace.block_number,
                    'block_timestamp': trace.block_timestamp
                })

    return pandas.DataFrame(addresses).drop_duplicates().to_dict(orient='records')


def coin_balances_rpc_requests(make_requests, addresses, is_batch):
    for idx, address in enumerate(addresses):
        address['request_id'] = idx

    coin_balance_rpc = list(generate_get_balance_json_rpc(addresses))

    if is_batch:
        response = make_requests(params=json.dumps(coin_balance_rpc))
    else:
        response = [make_requests(params=json.dumps(coin_balance_rpc[0]))]

    coin_balances = []
    for data in list(zip_rpc_response(addresses, response)):
        result = rpc_response_to_result(data[1])

        coin_balances.append({
            'address': data[0]['address'],
            'balance': to_int(hexstr=result),
            'block_number': data[0]['block_number'],
            'block_timestamp': data[0]['block_timestamp'],
        })

    return coin_balances
