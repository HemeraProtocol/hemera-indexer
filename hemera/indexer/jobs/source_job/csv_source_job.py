import logging
import os
from collections import defaultdict

import pandas

from hemera.indexer.domain import dict_to_dataclass, domains_mapping
from hemera.indexer.domain.block import Block, UpdateBlockInternalCount
from hemera.indexer.domain.block_ts_mapper import BlockTsMapper
from hemera.indexer.domain.coin_balance import CoinBalance
from hemera.indexer.domain.contract import Contract
from hemera.indexer.domain.contract_internal_transaction import ContractInternalTransaction
from hemera.indexer.domain.current_token_balance import CurrentTokenBalance
from hemera.indexer.domain.log import Log
from hemera.indexer.domain.token import Token, UpdateToken
from hemera.indexer.domain.token_balance import TokenBalance
from hemera.indexer.domain.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from hemera.indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.domain.trace import Trace
from hemera.indexer.domain.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseSourceJob
from hemera.indexer.utils.parameter_utils import extract_path_from_parameter

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
