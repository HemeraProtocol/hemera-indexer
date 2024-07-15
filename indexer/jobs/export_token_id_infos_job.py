import json
import logging

import pandas

from eth_abi import abi
from web3 import Web3

from indexer.domain.token_id_infos import format_erc721_token_id_change, format_erc721_token_id_detail, \
    format_erc1155_token_id_detail
from enumeration.entity_type import EntityType
from enumeration.token_type import TokenType
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from common.models.erc1155_token_id_details import ERC1155TokenIdDetails
from common.models.erc721_token_id_details import ERC721TokenIdDetails
from indexer.jobs.base_job import BaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor
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
    def __init__(
            self,
            index_keys,
            entity_types,
            web3,
            service,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter
        self._exist_token = {
            "ERC721": get_exist_token_ids(service, ERC721TokenIdDetails),
            "ERC1155": get_exist_token_ids(service, ERC1155TokenIdDetails)
        }

    def _start(self):
        super()._start()

    def _collect(self):

        token_721 = distinct_token_ids(self._exist_token, self._data_buff['token_transfer'], TokenType.ERC721)
        self._batch_work_executor.execute(token_721,
                                          self._collect_batch,
                                          total_items=len(token_721))

        self._batch_work_executor.wait()

        token_1155 = distinct_token_ids(self._exist_token, self._data_buff['token_transfer'], TokenType.ERC1155)
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
        if self._entity_types & EntityType.TOKEN_IDS:
            items = self._extract_from_buff(
                ['erc721_token_id_changes', 'erc721_token_id_details', 'erc1155_token_id_details'])
            self._item_exporter.export_items(items)


def get_exist_token_ids(db_service, model):
    session = db_service.get_service_session()
    try:

        result = session.query(model.address, model.token_id).all()
        history_token = [('0x' + item[0].hex(), item[1]) for item in result]

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return history_token


def distinct_token_ids(exist_tokens, token_transfers, token_type):
    exist_set = set(exist_tokens[token_type.value])

    unique_tokens = {}
    for token_transfer in token_transfers:
        if token_transfer['tokenType'] == token_type.value:
            key = f"{token_transfer['tokenAddress']}_{token_transfer['tokenId']}_{token_transfer['blockNumber']}"
            if key not in unique_tokens:
                is_new = True
                if (token_transfer['tokenAddress'], token_transfer['tokenId']) in exist_set:
                    is_new = False

                unique_tokens[key] = {
                    'address': token_transfer['tokenAddress'],
                    'token_id': token_transfer['tokenId'],
                    'token_type': token_transfer['tokenType'],
                    'block_number': token_transfer['blockNumber'],
                    'block_timestamp': token_transfer['blockTimestamp'],
                    'is_new': is_new,
                    'request_id': len(unique_tokens.keys())
                }

    tokens_list = []
    for key in unique_tokens.keys():
        tokens_list.append(unique_tokens[key])

    return tokens_list


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
