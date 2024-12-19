import logging
from itertools import groupby
from typing import List, Optional, Union

from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera.indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from hemera.indexer.domains.token_transfer import ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseExportJob
from hemera.indexer.utils.multicall_hemera.util import calculate_execution_time
from hemera.indexer.utils.token_fetcher import TokenFetcher

logger = logging.getLogger(__name__)


class ExportTokenIdInfosJob(BaseExportJob):
    dependency_types = [ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [
        ERC721TokenIdChange,
        ERC721TokenIdDetail,
        UpdateERC721TokenIdDetail,
        ERC1155TokenIdDetail,
        UpdateERC1155TokenIdDetail,
    ]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._is_multi_call = kwargs["multicall"]

        self.token_fetcher = TokenFetcher(self._web3, kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        token_id_info = generate_token_id_info(
            self._data_buff[ERC721TokenTransfer.type()],
            self._data_buff[ERC1155TokenTransfer.type()],
        )
        self._collect_batch(token_id_info)

    @calculate_execution_time
    def _collect_batch(self, token_list):
        items = self.token_fetcher.fetch_token_ids_info(token_list)
        for item in items:
            self._collect_item(item.type(), item)

    @calculate_execution_time
    def _process(self, **kwargs):
        self._data_buff[UpdateERC721TokenIdDetail.type()].sort(
            key=lambda x: (x.token_address, x.token_id, x.block_number)
        )
        self._data_buff[UpdateERC1155TokenIdDetail.type()].sort(
            key=lambda x: (x.token_address, x.token_id, x.block_number)
        )

        self._data_buff[UpdateERC721TokenIdDetail.type()] = [
            list(group)[-1]
            for key, group in groupby(
                self._data_buff[UpdateERC721TokenIdDetail.type()],
                lambda x: (x.token_address, x.token_id),
            )
        ]

        self._data_buff[UpdateERC1155TokenIdDetail.type()] = [
            list(group)[-1]
            for key, group in groupby(
                self._data_buff[UpdateERC1155TokenIdDetail.type()],
                lambda x: (x.token_address, x.token_id),
            )
        ]


def generate_token_id_info(
    erc721_token_transfers: List[ERC721TokenTransfer],
    erc1155_token_transfers: List[ERC1155TokenTransfer],
    block_number: Union[Optional[int], str] = None,
) -> List[dict]:
    info = []
    seen_keys = set()

    for token_transfer in erc721_token_transfers + erc1155_token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}_{token_transfer.block_number}"

        if key not in seen_keys:
            seen_keys.add(key)

            if token_transfer.from_address == ZERO_ADDRESS and block_number is None:
                info.append(
                    {
                        "address": token_transfer.token_address,
                        "token_id": token_transfer.token_id,
                        "token_type": token_transfer.token_type,
                        "block_number": token_transfer.block_number if block_number is None else block_number,
                        "block_timestamp": token_transfer.block_timestamp,
                        "is_get_token_uri": True,
                        "request_id": abs(hash(key + "_get_token_uri")),
                    }
                )

            info.append(
                {
                    "address": token_transfer.token_address,
                    "token_id": token_transfer.token_id,
                    "token_type": token_transfer.token_type,
                    "block_number": token_transfer.block_number if block_number is None else block_number,
                    "block_timestamp": token_transfer.block_timestamp,
                    "is_get_token_uri": False,
                    "request_id": abs(hash(key)),
                }
            )

    return info
