import json
import logging
from dataclasses import asdict, dataclass
from itertools import groupby
from typing import List

from eth_abi import abi

from common.utils.format_utils import to_snake_case
from enumeration.record_level import RecordLevel
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
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import ZERO_ADDRESS, rpc_response_to_result

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


@dataclass(frozen=True)
class TokenIdInfo:
    address: str
    token_id: int
    token_type: str
    block_number: int
    block_timestamp: int
    is_get_token_uri: bool
    request_id: int


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

    def _collect(self, **kwargs):
        token_id_info = generate_token_id_info(
            self._data_buff[ERC721TokenTransfer.type()],
            self._data_buff[ERC1155TokenTransfer.type()],
        )
        self._batch_work_executor.execute(token_id_info, self._collect_batch, total_items=len(token_id_info))
        self._batch_work_executor.wait()

    def _collect_batch(self, token_list):
        items = token_ids_info_rpc_requests(self._batch_web3_provider.make_request, token_list, self._is_batch)
        for item in items:
            self._collect_item(item.type(), item)

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
):
    info = set()
    for token_transfer in erc721_token_transfers + erc1155_token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}_{token_transfer.block_number}"
        if token_transfer.from_address == ZERO_ADDRESS:
            info.add(
                TokenIdInfo(
                    address=token_transfer.token_address,
                    token_id=token_transfer.token_id,
                    token_type=token_transfer.token_type,
                    block_number=token_transfer.block_number,
                    block_timestamp=token_transfer.block_timestamp,
                    is_get_token_uri=True,
                    request_id=hash(key + "_get_token_uri"),
                )
            )
        info.add(
            TokenIdInfo(
                address=token_transfer.token_address,
                token_id=token_transfer.token_id,
                token_type=token_transfer.token_type,
                block_number=token_transfer.block_number,
                block_timestamp=token_transfer.block_timestamp,
                is_get_token_uri=False,
                request_id=hash(key),
            )
        )

    return info


def abi_selector_encode_and_decode_type(token_id_info: TokenIdInfo):
    if token_id_info.token_type == TokenType.ERC721.value:
        if token_id_info.is_get_token_uri:
            return encode_abi(
                ERC721_TOKEN_URI_ABI_FUNCTION,
                [token_id_info.token_id],
                erc721_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC721_OWNER_OF_ABI_FUNCTION,
                [token_id_info.token_id],
                erc721_owner_of_sig_prefix,
            )
    elif token_id_info.token_type == TokenType.ERC1155.value:
        if token_id_info.is_get_token_uri:
            return encode_abi(
                ERC1155_TOKEN_URI_ABI_FUNCTION,
                [token_id_info.token_id],
                erc1155_token_uri_sig_prefix,
            )
        else:
            return encode_abi(
                ERC1155_TOTAL_SUPPLY_ABI_FUNCTION,
                [token_id_info.token_id],
                erc1155_token_supply_sig_prefix,
            )


def token_ids_info_rpc_requests(make_requests, token_info_items, is_batch):
    return_data = []
    eth_calls = list(
        generate_eth_call_json_rpc(
            [
                {
                    "request_id": item.request_id,
                    "param_to": item.address,
                    "param_data": abi_selector_encode_and_decode_type(item),
                    "param_number": hex(item.block_number),
                }
                for item in token_info_items
            ]
        )
    )

    if is_batch:
        response = make_requests(params=json.dumps(eth_calls))
    else:
        response = [make_requests(params=json.dumps(eth_calls[0]))]

    for token_info, data in zip(token_info_items, response):
        result = rpc_response_to_result(data)
        value = result[2:] if result is not None else None
        if value is None:
            continue
        try:
            if token_info.token_type == "ERC721":
                if token_info.is_get_token_uri:
                    return_data.append(
                        ERC721TokenIdDetail(
                            token_address=token_info.address,
                            token_id=token_info.token_id,
                            token_uri=abi.decode(["string"], bytes.fromhex(value))[0].replace("\u0000", ""),
                            block_number=token_info.block_number,
                            block_timestamp=token_info.block_timestamp,
                        )
                    )
                else:
                    return_data.append(
                        UpdateERC721TokenIdDetail(
                            token_address=token_info.address,
                            token_id=token_info.token_id,
                            token_owner=abi.decode(["address"], bytes.fromhex(value))[0],
                            block_number=token_info.block_number,
                            block_timestamp=token_info.block_timestamp,
                        )
                    )
                    return_data.append(
                        ERC721TokenIdChange(
                            token_address=token_info.address,
                            token_id=token_info.token_id,
                            token_owner=abi.decode(["address"], bytes.fromhex(value))[0],
                            block_number=token_info.block_number,
                            block_timestamp=token_info.block_timestamp,
                        )
                    )
            else:
                if token_info.is_get_token_uri:
                    return_data.append(
                        ERC1155TokenIdDetail(
                            token_address=token_info.address,
                            token_id=token_info.token_id,
                            token_uri=abi.decode(["string"], bytes.fromhex(value))[0].replace("\u0000", ""),
                            block_number=token_info.block_number,
                            block_timestamp=token_info.block_timestamp,
                        )
                    )
                else:
                    return_data.append(
                        UpdateERC1155TokenIdDetail(
                            token_address=token_info.address,
                            token_id=token_info.token_id,
                            token_supply=abi.decode(["uint256"], bytes.fromhex(value))[0],
                            block_number=token_info.block_number,
                            block_timestamp=token_info.block_timestamp,
                        )
                    )
        except Exception as e:
            logger.warning(
                f"Decoding token id info failed. "
                f"token address: {token_info.address}. "
                f"rpc response: {result}. "
                f"block number: {token_info.block_number}. "
                f"exception: {e}. "
            )
            exception_recorder.log(
                block_number=token_info.block_number,
                dataclass=to_snake_case(TokenIdInfo.__name__),
                message_type="decode_token_id_info_fail",
                message=str(e),
                exception_env=asdict(token_info),
                level=RecordLevel.WARN,
            )
    return return_data
