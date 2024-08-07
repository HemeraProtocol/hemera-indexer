import logging
from dataclasses import asdict, dataclass
from itertools import groupby
from typing import List

from enumeration.token_type import TokenType
from indexer.domain.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from indexer.domain.token_transfer import ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.modules.bridge.signature import function_abi_to_4byte_selector_str
from indexer.utils.abi import encode_abi
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.multi_call_util import MultiCallProxy
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()

ERC721_TOKEN_URI_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "tokenURI",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC721_OWNER_OF_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "ownerOf",
    "outputs": [{"name": "", "type": "address"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC1155_TOKEN_URI_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "uri",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

ERC1155_TOTAL_SUPPLY_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "id", "type": "uint256"}],
    "name": "totalSupply",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

erc721_uri_sig_prefix = function_abi_to_4byte_selector_str(ERC721_TOKEN_URI_ABI_FUNCTION)
erc721_owner_of_sig_prefix = function_abi_to_4byte_selector_str(ERC721_OWNER_OF_ABI_FUNCTION)

erc1155_token_uri_sig_prefix = function_abi_to_4byte_selector_str(ERC1155_TOKEN_URI_ABI_FUNCTION)
erc1155_token_supply_sig_prefix = function_abi_to_4byte_selector_str(ERC1155_TOTAL_SUPPLY_ABI_FUNCTION)


class ExportTokenIdInfosJob(BaseExportJob):
    dependency_types = [ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [
        ERC721TokenIdChange,
        ERC721TokenIdDetail,
        UpdateERC721TokenIdDetail,
        ERC1155TokenIdDetail,
        UpdateERC1155TokenIdDetail,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self.multi_call_util = MultiCallProxy(self._web3, kwargs)

    def _start(self):
        super()._start()

    @calculate_execution_time
    def _collect(self, **kwargs):
        token_id_info = generate_token_id_info(
            self._data_buff[ERC721TokenTransfer.type()],
            self._data_buff[ERC1155TokenTransfer.type()],
        )

        self._collect_batch(token_id_info)

    @calculate_execution_time
    def _collect_batch(self, token_list):
        items = self.multi_call_util.fetch_token_ids_info(token_list)
        for item in items:
            self._collect_item(item.type(), item)

    def _process(self):
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
) -> List[dict]:
    info = []
    seen_keys = set()

    for token_transfer in erc721_token_transfers + erc1155_token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}_{token_transfer.block_number}"

        if key not in seen_keys:
            seen_keys.add(key)

            if token_transfer.from_address == ZERO_ADDRESS:
                info.append(
                    {
                        "address": token_transfer.token_address,
                        "token_id": token_transfer.token_id,
                        "token_type": token_transfer.token_type,
                        "block_number": token_transfer.block_number,
                        "block_timestamp": token_transfer.block_timestamp,
                        "is_get_token_uri": True,
                        "request_id": hash(key + "_get_token_uri"),
                    }
                )

            info.append(
                {
                    "address": token_transfer.token_address,
                    "token_id": token_transfer.token_id,
                    "token_type": token_transfer.token_type,
                    "block_number": token_transfer.block_number,
                    "block_timestamp": token_transfer.block_timestamp,
                    "is_get_token_uri": False,
                    "request_id": hash(key),
                }
            )

    return info


def abi_selector_encode_and_decode_type(token_id_info):
    if token_id_info["token_type"] == TokenType.ERC721.value:
        if token_id_info["is_get_token_uri"]:
            return encode_abi(
                ERC721_TOKEN_URI_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc721_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC721_OWNER_OF_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc721_owner_of_sig_prefix,
            )
    elif token_id_info["token_type"] == TokenType.ERC1155.value:
        if token_id_info["is_get_token_uri"]:
            return encode_abi(
                ERC1155_TOKEN_URI_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc1155_token_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC1155_TOTAL_SUPPLY_ABI_FUNCTION,
                [token_id_info["token_id"]],
                erc1155_token_supply_sig_prefix,
            )
