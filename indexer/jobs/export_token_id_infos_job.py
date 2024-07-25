import json
import logging
from collections import defaultdict
from dataclasses import dataclass, replace, asdict
from typing import List

from eth_abi import abi
from web3 import Web3

from enumeration.token_type import TokenType
from indexer.domain.token_id_infos import ERC721TokenIdChange, ERC721TokenIdDetail, UpdateERC721TokenIdDetail, \
    ERC1155TokenIdDetail, UpdateERC1155TokenIdDetail
from indexer.domain.token_transfer import ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response, ZERO_ADDRESS

logger = logging.getLogger(__name__)
erc_token_id_info_abi = {
    "ERC721": [
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "tokenURI",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
            'require_new': True
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
            "require_new": False
        },
    ],
    "ERC1155": [
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "uri",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
            'require_new': True
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
            "require_new": False
        }
    ]
}


@dataclass(frozen=True)
class TokenIdInfo:
    address: str
    token_id: int
    token_type: str
    block_number: int
    block_timestamp: int
    is_get_token_uri: bool
    request_id: int


class ExportTokenIdInfosJob(BaseJob):
    dependency_types = [ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [
        ERC721TokenIdChange,
        ERC721TokenIdDetail,
        UpdateERC721TokenIdDetail,
        ERC1155TokenIdDetail,
        UpdateERC1155TokenIdDetail
    ]

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__)
        self._is_batch = kwargs['batch_size'] > 1

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):

        token_id_info = generate_token_id_info(
            self._data_buff[ERC721TokenTransfer.type()],
            self._data_buff[ERC1155TokenTransfer.type()]
        )
        self._batch_work_executor.execute(
            token_id_info,
            self._collect_batch,
            total_items=len(token_id_info))
        self._batch_work_executor.wait()

        self._batch_work_executor.wait()

    def _collect_batch(self, token_list):
        items = token_ids_info_rpc_requests(
            self._web3,
            self._batch_web3_provider.make_request,
            token_list,
            self._is_batch
        )
        for item in items:
            if item['token_type'] == TokenType.ERC721.value:
                self._collect_item(ERC721TokenIdChange.type(), item)
                if item['is_get_token_uri']:
                    self._collect_item(ERC721TokenIdDetail.type(), item)
                else:
                    self._collect_item(UpdateERC721TokenIdDetail.type(), item)
            elif item['token_type'] == TokenType.ERC1155.value:
                if item['is_get_token_uri']:
                    self._collect_item(ERC1155TokenIdDetail.type(), item)
                else:
                    self._collect_item(UpdateERC1155TokenIdDetail.type(), item)
            else:
                raise ValueError(f"Unknown token type: {item['token_type']}")


def generate_token_id_info(
        erc721_token_transfers: List[ERC721TokenTransfer],
        erc1155_token_transfers: List[ERC1155TokenTransfer]
):
    info = set()
    for token_transfer in erc721_token_transfers + erc1155_token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}_{token_transfer.block_number}"
        need_call_uri = token_transfer.from_address == ZERO_ADDRESS
        info.add(TokenIdInfo(
            address=token_transfer.token_address,
            token_id=token_transfer.token_id,
            token_type=token_transfer.token_type,
            block_number=token_transfer.block_number,
            block_timestamp=token_transfer.block_timestamp,
            is_get_token_uri=need_call_uri,
            request_id=hash(key)
        ))

    return info


def build_rpc_method_data(web3, tokens: List[TokenIdInfo], token_type, fn, require_new):
    parameters = []

    for token in tokens:

        if not token.is_get_token_uri and require_new:
            continue
        param = {
            'request_id': token.request_id,
            'param_to': token.address,
            'param_data': '0x',
            'param_number': hex(token.block_number)
        }

        try:
            param['param_data'] = (web3.eth
                                   .contract(address=Web3.to_checksum_address(token.address),
                                             abi=erc_token_id_info_abi[token_type])
                                   .encodeABI(fn_name=fn, args=[token.token_id]))
        except Exception as e:
            logger.warning(f"Encoding token id {fn} abi parameter failed. "
                           f"token address: {token.address}. "
                           f"token id: {token.token_id}. "
                           f"exception: {e}. ")

        for abi_fn in erc_token_id_info_abi[token_type]:
            if fn == abi_fn['name']:
                param['data_type'] = abi_fn['outputs'][0]['type']
        parameters.append(param)
    return parameters


def token_ids_info_rpc_requests(web3, make_requests, token_info_items, is_batch):
    grouped_tokens = defaultdict(list)
    for token in token_info_items:
        grouped_tokens[token.token_type].append(token)

    for token_type, tokens in grouped_tokens.items():
        for abi_json in erc_token_id_info_abi[token_type]:
            token_name_rpc = list(generate_eth_call_json_rpc(
                build_rpc_method_data(web3, tokens, token_type, abi_json['name'], abi_json['require_new'])))

            if len(token_name_rpc) == 0:
                continue

            if is_batch:
                response = make_requests(params=json.dumps(token_name_rpc))
            else:
                response = [make_requests(params=json.dumps(token_name_rpc[0]))]

            for token, data in zip(tokens, response):
                result = rpc_response_to_result(data)

                value = result[2:] if result is not None else None
                try:
                    decoded_value = abi.decode([abi_json['data_type']], bytes.fromhex(value))[0]
                    if abi_json['data_type'] == 'string':
                        decoded_value = decoded_value.replace('\u0000', '')

                    # Create a new TokenIdInfo object with the updated field
                    token = replace(token, **{abi_json['name']: decoded_value})
                except Exception as e:
                    logger.warning(f"Decoding token id {abi_json['name']} failed. "
                                   f"token: {asdict(token)}. "
                                   f"rpc response: {result}. "
                                   f"exception: {e}.")
                    token = replace(token, **{abi_json['name']: None})

    return token_info_items
