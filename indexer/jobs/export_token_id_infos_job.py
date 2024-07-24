import json
import logging
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
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

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


class ExportTokenIdInfosJob(BaseJob):

    dependency_types = [ERC721TokenTransfer, ERC721TokenTransfer]
    output_types = [
        ERC721TokenIdChange,
        ERC721TokenIdDetail,
        UpdateERC721TokenIdDetail,
        ERC1155TokenIdDetail,
        UpdateERC1155TokenIdDetail
    ]

    def __init__(
            self,
            entity_types,
            web3,
            service,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(entity_types=entity_types)

        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter
        self._erc721_token_ids = []
        self._erc1155_token_ids = []

    def _start(self):
        super()._start()

    def _collect(self,  **kwargs):

        if ERC721TokenTransfer.type() in self._data_buff:
            token_721 = distinct_erc721_token_ids(self._exist_token['ERC721'],
                                                  self._data_buff[ERC721TokenTransfer.type()])
            self._batch_work_executor.execute(token_721,
                                              self._collect_batch,
                                              total_items=len(token_721))
            self._batch_work_executor.wait()

        if ERC1155TokenTransfer.type() in self._data_buff:
            token_1155 = distinct_erc1155_token_ids(self._exist_token['ERC1155'],
                                                    self._data_buff[ERC1155TokenTransfer.type()])
            self._batch_work_executor.execute(token_1155,
                                              self._collect_batch,
                                              total_items=len(token_1155))

        self._batch_work_executor.shutdown()

    def _collect_batch(self, token_list):
        tokens = token_ids_info_rpc_requests(self._web3,
                                             self._batch_web3_provider.make_request,
                                             token_list,
                                             self._is_batch)
        for token in tokens:
            if token['token_type'] == TokenType.ERC721.value:
                self._erc721_token_ids.append(token)
            else:
                self._erc1155_token_ids.append(token)

    def _process(self):

        if len(self._erc721_token_ids) > 0:
            self._data_buff[ERC721TokenIdChange.type()] = [ERC721TokenIdChange(token_id_info)
                                                           for token_id_info in self._erc721_token_ids]

            self._data_buff[ERC721TokenIdDetail.type()] = [ERC721TokenIdDetail(token_id_info)
                                                           for token_id_info in self._erc721_token_ids
                                                           if token_id_info['is_new']]

            self._data_buff[UpdateERC721TokenIdDetail.type()] = [UpdateERC721TokenIdDetail(token_id_info)
                                                                 for token_id_info in self._erc721_token_ids
                                                                 if not token_id_info['is_new']]

        if len(self._erc1155_token_ids) > 0:
            self._data_buff[ERC1155TokenIdDetail.type()] = [ERC1155TokenIdDetail(token_id_info)
                                                            for token_id_info in self._erc1155_token_ids
                                                            if token_id_info['is_new']]

            self._data_buff[UpdateERC1155TokenIdDetail.type()] = [UpdateERC1155TokenIdDetail(token_id_info)
                                                                  for token_id_info in self._erc1155_token_ids
                                                                  if not token_id_info['is_new']]


def distinct_erc721_token_ids(exist_tokens: list, token_transfers: List[ERC721TokenTransfer]):
    exist_set = set(exist_tokens)
    dealt_set = set()
    unique_tokens = {}
    for token_transfer in token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}_{token_transfer.block_number}"
        if key not in unique_tokens:
            is_new = True
            key = (token_transfer.token_address, token_transfer.token_id)
            if key in exist_set or key in dealt_set:
                is_new = False

            if key in dealt_set and unique_tokens[key]['block_number'] < token_transfer.block_number:
                unique_tokens[key]['block_number'] = token_transfer.block_number
                unique_tokens[key]['block_timestamp'] = token_transfer.block_timestamp
            else:
                unique_tokens[key] = {
                    'address': token_transfer.token_address,
                    'token_id': token_transfer.token_id,
                    'token_type': token_transfer.token_type,
                    'block_number': token_transfer.block_number,
                    'block_timestamp': token_transfer.block_timestamp,
                    'is_new': is_new,
                    'request_id': len(unique_tokens.keys())
                }
            dealt_set.add(key)

    return [unique_tokens[key] for key in unique_tokens.keys()]


def distinct_erc1155_token_ids(exist_tokens: list, token_transfers: List[ERC1155TokenTransfer]):
    exist_set = set(exist_tokens)

    unique_tokens = {}
    for token_transfer in token_transfers:
        key = f"{token_transfer.token_address}_{token_transfer.token_id}"
        if key not in unique_tokens:
            is_new = True
            if (token_transfer.token_address, token_transfer.token_id) in exist_set:
                is_new = False

            unique_tokens[key] = {
                'address': token_transfer.token_address,
                'token_id': token_transfer.token_id,
                'token_type': token_transfer.token_type,
                'block_number': token_transfer.block_number,
                'block_timestamp': token_transfer.block_timestamp,
                'is_new': is_new,
                'request_id': len(unique_tokens.keys())
            }
        else:
            if unique_tokens[key]['block_number'] < token_transfer.block_number:
                unique_tokens[key]['block_number'] = token_transfer.block_number
                unique_tokens[key]['block_timestamp'] = token_transfer.block_timestamp

    return [unique_tokens[key] for key in unique_tokens.keys()]


def build_rpc_method_data(web3, tokens, token_type, fn, require_new):
    parameters = []

    for token in tokens:

        if not token['is_new'] and require_new:
            continue

        token['param_to'] = token['address']
        token['param_data'] = '0x'
        token['param_number'] = hex(token['block_number'])

        try:
            token['param_data'] = (web3.eth
                                   .contract(address=Web3.to_checksum_address(token['address']),
                                             abi=erc_token_id_info_abi[token_type])
                                   .encodeABI(fn_name=fn, args=[token['token_id']]))
        except Exception as e:
            logger.warning(f"Encoding token id {fn} abi parameter failed. "
                           f"token address: {token['address']}. "
                           f"token id: {token['token_id']}. "
                           f"exception: {e}. ")

        for abi_fn in erc_token_id_info_abi[token_type]:
            if fn == abi_fn['name']:
                token['data_type'] = abi_fn['outputs'][0]['type']
        parameters.append(token)
    return parameters


def token_ids_info_rpc_requests(web3, make_requests, tokens, is_batch):
    token_type = tokens[0]['token_type']
    for abi_json in erc_token_id_info_abi[token_type]:
        token_name_rpc = list(generate_eth_call_json_rpc(
            build_rpc_method_data(web3, tokens, token_type, abi_json['name'], abi_json['require_new'])))

        if len(token_name_rpc) == 0:
            continue

        if is_batch:
            response = make_requests(params=json.dumps(token_name_rpc))
        else:
            response = [make_requests(params=json.dumps(token_name_rpc[0]))]

        for data in list(zip_rpc_response(tokens, response)):
            result = rpc_response_to_result(data[1], ignore_errors=True)

            token = data[0]
            value = result[2:] if result is not None else None
            try:
                token[abi_json['name']] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                if token['data_type'] == 'string':
                    token[abi_json['name']] = token[abi_json['name']].replace('\u0000', '')
            except Exception as e:
                logger.warning(f"Decoding token id {abi_json['name']} failed. "
                               f"token: {token}. "
                               f"rpc response: {result}. "
                               f"exception: {e}.")
                token[abi_json['name']] = None

    return tokens
