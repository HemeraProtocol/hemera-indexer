import json
import pandas

from eth_abi import abi
from eth_abi.exceptions import InsufficientDataBytes
from web3 import Web3

from domain.token_id_infos import format_erc721_token_id_change, format_erc721_token_id_detail, \
    format_erc1155_token_id_detail
from enumeration.entity_type import EntityType
from enumeration.token_type import TokenType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_eth_call_json_rpc
from utils.utils import rpc_response_to_result

erc_token_id_info_abi = {
    "ERC721": [
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "tokenURI",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
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
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
}


class ExportTokenIdInfosJob(BaseJob):
    def __init__(
            self,
            index_keys,
            entity_types,
            web3,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        erc721_token_list = []
        erc1155_token_list = []
        for token_transfer in self._data_buff['token_transfer']:
            if token_transfer['tokenType'] == TokenType.ERC721.value:
                erc721_token_list.append({
                    'address': token_transfer['tokenAddress'],
                    'token_id': token_transfer['tokenId'],
                    'token_type': token_transfer['tokenType'],
                    'block_number': token_transfer['blockNumber'],
                    'block_timestamp': token_transfer['blockTimestamp'],
                })
            elif token_transfer['tokenType'] == TokenType.ERC1155.value:
                erc1155_token_list.append({
                    'address': token_transfer['tokenAddress'],
                    'token_id': token_transfer['tokenId'],
                    'token_type': token_transfer['tokenType'],
                    'block_number': token_transfer['blockNumber'],
                    'block_timestamp': token_transfer['blockTimestamp'],
                })

        unique_token = pandas.DataFrame(erc721_token_list).drop_duplicates()
        self._batch_work_executor.execute(unique_token.to_dict(orient="records"), self._collect_batch)
        unique_token = pandas.DataFrame(erc1155_token_list).drop_duplicates()
        self._batch_work_executor.execute(unique_token.to_dict(orient="records"), self._collect_batch)

        self._batch_work_executor.shutdown()

    def _collect_batch(self, token_list):
        tokens = self._fetch_token_id_info(token_list)
        for token in tokens:
            if token['token_type'] == TokenType.ERC721.value:
                token['item'] = 'erc721_token_ids'
            else:
                token['item'] = 'erc1155_token_ids'
            self._collect_item(token)

    def _process(self):

        if len(self._data_buff['erc721_token_ids']) > 0:
            self._data_buff['erc721_token_id_changes'] = [format_erc721_token_id_change(token_id_info)
                                                          for token_id_info in self._data_buff['erc721_token_ids']]

            total_erc721_id_details = pandas.DataFrame([format_erc721_token_id_detail(token_id_info)
                                                        for token_id_info in self._data_buff['erc721_token_ids']])
            self._data_buff['erc721_token_id_details'] = total_erc721_id_details.loc[total_erc721_id_details.groupby(
                ['address', 'token_id'])['block_number'].idxmax()].to_dict(orient='records')

        if len(self._data_buff['erc1155_token_ids']) > 0:
            total_erc1155_id_details = pandas.DataFrame([format_erc1155_token_id_detail(token_id_info)
                                                         for token_id_info in self._data_buff['erc1155_token_ids']])
            self._data_buff['erc1155_token_id_details'] = total_erc1155_id_details.loc[total_erc1155_id_details.groupby(
                ['address', 'token_id'])['block_number'].idxmax()].to_dict(orient='records')

    def _export(self):
        if self._entity_types & EntityType.TOKEN:
            items = self._extract_from_buff(
                ['erc721_token_id_changes', 'erc721_token_id_details', 'erc1155_token_id_details'])
            self._item_exporter.export_items(items)

    def _build_rpc_method_data(self, tokens, token_type, fn):
        parameters = []

        for token in tokens:
            token['param_to'] = token['address']
            token['param_data'] = (self._web3.eth
                                   .contract(address=Web3.to_checksum_address(token['address']),
                                             abi=erc_token_id_info_abi[token_type])
                                   .encodeABI(fn_name=fn, args=[token['token_id']]))
            for abi_fn in erc_token_id_info_abi[token_type]:
                if fn == abi_fn['name']:
                    token['data_type'] = abi_fn['outputs'][0]['type']
            parameters.append(token)
        return parameters

    def _fetch_token_id_info(self, tokens):
        token_type = tokens[0]['token_type']
        for abi_json in erc_token_id_info_abi[token_type]:
            token_name_rpc = list(generate_eth_call_json_rpc(
                self._build_rpc_method_data(tokens, token_type, abi_json['name'])))
            response = self._batch_web3_provider.make_batch_request(json.dumps(token_name_rpc))
            for data in list(zip(response, tokens)):
                result = rpc_response_to_result(data[0], ignore_errors=True)

                token = data[1]
                value = result[2:] if result is not None else None
                try:
                    token[abi_json['name']] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                    if token['data_type'] == 'string':
                        token[abi_json['name']] = token[abi_json['name']].replace('\u0000', '')
                except (InsufficientDataBytes, TypeError) as e:
                    token[abi_json['name']] = None

        return tokens
