import json
import logging
from dataclasses import dataclass
from typing import List

from eth_utils import to_int

from common.utils.exception_control import RPCNotReachable
from indexer.domain.block import Block
from indexer.domain.coin_balance import CoinBalance
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.utils.json_rpc_requests import generate_get_balance_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddressRecord:
    address: str
    block_number: int
    block_timestamp: int


# Exports coin balances
class ExportCoinBalancesJob(BaseJob):
    dependency_types = [Block, ContractInternalTransaction]
    output_types = [CoinBalance]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        coin_addresses = distinct_addresses(
            self._data_buff[Block.type()],
            self._data_buff[Transaction.type()],
            self._data_buff[ContractInternalTransaction.type()],
        )
        self._batch_work_executor.execute(coin_addresses, self._collect_batch, total_items=len(coin_addresses))
        self._batch_work_executor.wait()

    def _collect_batch(self, coin_addresses):
        coin_balances = coin_balances_rpc_requests(
            self._batch_web3_provider.make_request, coin_addresses, self._is_batch
        )

        for coin_balance in coin_balances:
            self._collect_item(CoinBalance.type(), CoinBalance(coin_balance))

    def _process(self):
        self._data_buff[CoinBalance.type()].sort(key=lambda x: (x.block_number, x.address))


def distinct_addresses(blocks: List[Block], transactions: List[Transaction], traces: List[ContractInternalTransaction]):
    unique_addresses = set()
    for block in blocks:
        unique_addresses.add(
            AddressRecord(
                address=block.miner,
                block_number=block.number,
                block_timestamp=block.timestamp,
            )
        )

    for transaction in transactions:
        if transaction.from_address is not None:
            unique_addresses.add(
                AddressRecord(
                    address=transaction.from_address,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                )
            )

        if transaction.to_address is not None:
            unique_addresses.add(
                AddressRecord(
                    address=transaction.to_address,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                )
            )

    for trace in traces:
        if trace.to_address is not None:
            unique_addresses.add(
                AddressRecord(
                    address=trace.to_address,
                    block_number=trace.block_number,
                    block_timestamp=trace.block_timestamp,
                )
            )
        if trace.from_address is not None:
            unique_addresses.add(
                AddressRecord(
                    address=trace.from_address,
                    block_number=trace.block_number,
                    block_timestamp=trace.block_timestamp,
                )
            )
    return [record.__dict__ for record in unique_addresses]


def coin_balances_rpc_requests(make_requests, addresses, is_batch):
    for idx, address in enumerate(addresses):
        address["request_id"] = idx

    coin_balance_rpc = list(generate_get_balance_json_rpc(addresses))

    if is_batch:
        response = make_requests(params=json.dumps(coin_balance_rpc))
    else:
        response = [make_requests(params=json.dumps(coin_balance_rpc[0]))]

    coin_balances = []
    for data in list(zip_rpc_response(addresses, response)):
        try:
            result = rpc_response_to_result(data[1])
        except RPCNotReachable as e:
            result = None
            # logger.warning("eth call failed: %s", e)
        coin_balances.append(
            {
                "address": data[0]["address"],
                "balance": to_int(hexstr=result) if result else None,
                "block_number": data[0]["block_number"],
                "block_timestamp": data[0]["block_timestamp"],
            }
        )

    return coin_balances
