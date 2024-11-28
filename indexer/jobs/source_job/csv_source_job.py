import logging
import os
from collections import defaultdict

import pandas

from indexer.domains import dict_to_dataclass, domains_mapping
from indexer.domains.block import Block, UpdateBlockInternalCount
from indexer.domains.block_ts_mapper import BlockTsMapper
from indexer.domains.coin_balance import CoinBalance
from indexer.domains.contract import Contract
from indexer.domains.contract_internal_transaction import ContractInternalTransaction
from indexer.domains.current_token_balance import CurrentTokenBalance
from indexer.domains.log import Log
from indexer.domains.token import Token, UpdateToken
from indexer.domains.token_balance import TokenBalance
from indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.domains.trace import Trace
from indexer.domains.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseSourceJob
from indexer.utils.parameter_utils import extract_path_from_parameter

logger = logging.getLogger(__name__)


class CSVSourceJob(BaseSourceJob):
    output_types = [
        Block,
        BlockTsMapper,
        Transaction,
        Log,
        Token,
        UpdateToken,
        ERC20TokenTransfer,
        ERC721TokenTransfer,
        ERC1155TokenTransfer,
        ERC721TokenIdChange,
        ERC721TokenIdDetail,
        UpdateERC721TokenIdDetail,
        ERC1155TokenIdDetail,
        UpdateERC1155TokenIdDetail,
        TokenBalance,
        CurrentTokenBalance,
        Trace,
        ContractInternalTransaction,
        UpdateBlockInternalCount,
        Contract,
        CoinBalance,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._source_path = extract_path_from_parameter(kwargs["config"].get("source_path"))
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._dataclass_mapping = scan_datas_file(self._source_path)

    def _collect(self, **kwargs):
        self._start_block = int(kwargs["start_block"])
        self._end_block = int(kwargs["end_block"])

        for key in self._dataclass_mapping.keys():
            target_files = []
            for domain_info in self._dataclass_mapping[key]:
                data_range = domain_info["data_range"]
                if self._start_block >= data_range[0] and self._end_block <= data_range[1]:
                    target_files.append(
                        os.path.join(domain_info["dir_path"], f"{key}-{data_range[0]}-{data_range[1]}.csv")
                    )

            for file in target_files:
                items = pandas.read_csv(file).to_dict(orient="records")
                for item in items:
                    if (
                        ("number" in item and self._start_block <= item["number"] <= self._end_block)
                        or "block_number" in item
                        and self._start_block <= item["block_number"] <= self._end_block
                    ):
                        self._collect_item(key, dict_to_dataclass(item, domains_mapping[key]))


def scan_datas_file(files_path) -> dict[str, list[dict]]:
    dataclass_mapping = defaultdict(list)
    for root, dirs, files in os.walk(files_path):
        for file in files:
            name_compose = file[:-4].split("-")
            domain = name_compose[0]
            blocks_range = (int(name_compose[1]), int(name_compose[2]))
            dataclass_mapping[domain].append(
                {
                    "dir_path": root,
                    "data_range": blocks_range,
                }
            )

    return dataclass_mapping
