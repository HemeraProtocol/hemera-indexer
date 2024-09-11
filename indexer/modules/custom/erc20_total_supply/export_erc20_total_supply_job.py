import configparser
import logging
import os
from collections import defaultdict

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.erc20_total_supply import constants
from indexer.modules.custom.erc20_total_supply.domain.erc20_total_supply import (
    Erc20CurrentTotalSupply,
    Erc20TotalSupply,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportErc20TotalSupplyJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [Erc20TotalSupply, Erc20CurrentTotalSupply]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self._need_collected_list),
            ]
        )

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            address_list_str = config.get(str(chain_id), "address_list", fallback="")
            self._need_collected_list = [address.strip() for address in address_list_str.split(",") if address.strip()]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        if self._need_collected_list is None or len(self._need_collected_list) == 0:
            return
        token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        # filter and group
        if token_transfers is None or len(token_transfers) == 0:
            return
        self._batch_work_executor.execute(
            token_transfers,
            self._collect_batch,
            total_items=len(token_transfers),
            split_method=split_token_transfers,
        )

        self._batch_work_executor.wait()

    def _collect_batch(self, token_transfers) -> None:
        if token_transfers is None or len(token_transfers) == 0:
            return
        token_address = next(iter(token_transfers))
        if token_address not in self._need_collected_list:
            return
        grouped_block = {}
        max_block_number = 0
        for entity in token_transfers[token_address]:
            block_number = entity.block_number
            grouped_block[block_number] = entity.block_timestamp
            if block_number > max_block_number:
                max_block_number = block_number

        # collect total supply
        total_supply_infos = collect_pool_total_supply(
            list(grouped_block.keys()),
            token_address,
            constants.ABI,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._batch_size,
            self._max_worker,
        )
        for data in total_supply_infos:
            block_number = data["block_number"]
            block_timestamp = grouped_block[block_number]
            total_supply = data["totalSupply"]

            self._collect_item(
                Erc20TotalSupply.type(),
                parse_to_total_supply(block_number, block_timestamp, token_address, total_supply),
            )

            if block_number == max_block_number:
                self._collect_item(
                    Erc20CurrentTotalSupply.type(),
                    Erc20CurrentTotalSupply(
                        token_address=token_address,
                        total_supply=total_supply,
                        block_number=block_number,
                        block_timestamp=block_timestamp,
                    ),
                )

    def _process(self, **kwargs):

        self._data_buff[Erc20TotalSupply.type()].sort(key=lambda x: x.block_number)
        self._data_buff[Erc20CurrentTotalSupply.type()].sort(key=lambda x: x.block_number)


def parse_to_total_supply(block_number, block_timestamp, address, total_supply):
    return Erc20TotalSupply(
        token_address=address,
        total_supply=total_supply,
        block_number=block_number,
        block_timestamp=block_timestamp,
    )


def collect_pool_total_supply(
    block_number_set, contract_address, abi_list, web3, make_requests, is_batch, batch_size, max_worker
):
    need_collect_list = []
    for block_number in block_number_set:
        need_collect_list.append({"address": contract_address, "block_number": block_number})

    # call totalSupply
    total_supply_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, need_collect_list, is_batch, abi_list, "totalSupply", "address", batch_size, max_worker
    )

    return total_supply_infos


def split_token_transfers(token_transfers):
    token_transfer_dict = defaultdict(list)
    for data in token_transfers:
        token_transfer_dict[data.token_address].append(data)

    for token_address, data in token_transfer_dict.items():
        yield {token_address: data}
