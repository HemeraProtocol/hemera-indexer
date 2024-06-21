import json

from eth_abi import abi
from web3 import Web3
from web3.exceptions import Web3ValidationError

from domain.token import format_token_data
from domain.token_transfer import extract_transfer_from_log, \
    format_erc20_token_transfer_data, format_erc721_token_transfer_data, format_erc1155_token_transfer_data
from enumeration.entity_type import EntityType
from enumeration.token_type import TokenType
from exporters.console_item_exporter import ConsoleItemExporter
from exporters.jdbc.schema.tokens import Tokens
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.enrich import enrich_blocks_timestamp
from utils.json_rpc_requests import generate_eth_call_json_rpc
from utils.utils import rpc_response_to_result

erc_token_abi = {
    "ELSE": [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }],
    "ERC1155": [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "tokenSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
}

erc_abi_names = {
    "ELSE": [abi_fn['name'] for abi_fn in erc_token_abi["ELSE"]],
    "ERC1155": [abi_fn['name'] for abi_fn in erc_token_abi["ERC1155"]]
}


class ExportTokensAndTransfersJob(BaseJob):
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
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter
        self._exist_token = self._get_exist_token(service)

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(self._data_buff['log'], self._collect_batch)
        self._batch_work_executor.shutdown()

    def _collect_batch(self, log_dicts):
        token_transfer = []
        for log_dict in log_dicts:
            transfer_event = extract_transfer_from_log(log_dict)
            if transfer_event is not None:
                if type(transfer_event) is list:
                    token_transfer.extend(transfer_event)
                else:
                    token_transfer.append(transfer_event)

        new_tokens = set()
        for token in token_transfer:
            if token['tokenAddress'][2:] not in self._exist_token.keys():
                new_tokens.add((token['tokenAddress'], token['tokenType']))
            elif token['tokenType'] is None:
                token['tokenType'] = self._exist_token[token['tokenAddress'][2:]]

        tokens_parameter = []
        for token in new_tokens:
            tokens_parameter.append(
                {
                    "address": token[0],
                    "token_type": token[1]
                }
            )

        new_token_types = {}
        if len(tokens_parameter) > 0:
            tokens = self._fetch_token_info(tokens_parameter)
            for token in tokens:
                if token['token_type'] is None:
                    if token['decimals'] is not None and token['decimals'] > 0:
                        token['token_type'] = TokenType.ERC20.value
                    else:
                        token['token_type'] = TokenType.ERC721.value
                self._collect_item(token)
                new_token_types[token['address']] = token['token_type']

        for transfer_event in token_transfer:
            if transfer_event['tokenType'] is None:
                transfer_event['tokenType'] = new_token_types[transfer_event['tokenAddress']]
            if transfer_event['tokenType'] == TokenType.ERC721.value:
                transfer_event['tokenId'] = transfer_event['value']
            self._collect_item(transfer_event)

    def _process(self):

        for token_transfer in enrich_blocks_timestamp(self._data_buff['block'], self._data_buff['token_transfer']):
            if token_transfer['tokenType'] == TokenType.ERC20.value:
                self._data_buff['erc20_token_transfers'].append(format_erc20_token_transfer_data(token_transfer))
            elif token_transfer['tokenType'] == TokenType.ERC721.value:
                self._data_buff['erc721_token_transfers'].append(format_erc721_token_transfer_data(token_transfer))
            elif token_transfer['tokenType'] == TokenType.ERC1155.value:
                self._data_buff['erc1155_token_transfers'].append(format_erc1155_token_transfer_data(token_transfer))

        self._data_buff['formated_token'] = [format_token_data(token) for token in self._data_buff['token']]

        self._data_buff['erc20_token_transfers'] = sorted(self._data_buff['erc20_token_transfers'],
                                                          key=lambda x: (
                                                              x['block_number'],
                                                              x['transaction_hash'],
                                                              x['log_index']))

        self._data_buff['erc721_token_transfers'] = sorted(self._data_buff['erc721_token_transfers'],
                                                           key=lambda x: (
                                                               x['block_number'],
                                                               x['transaction_hash'],
                                                               x['log_index']))

        self._data_buff['erc1155_token_transfers'] = sorted(self._data_buff['erc1155_token_transfers'],
                                                            key=lambda x: (
                                                                x['block_number'],
                                                                x['transaction_hash'],
                                                                x['log_index']))

    def _export(self):
        items = []

        if self._entity_types & EntityType.TOKEN:
            items.extend(self._extract_from_buff(['formated_token']))

        if self._entity_types & EntityType.TOKEN_TRANSFER:
            items.extend(
                self._extract_from_buff(['erc20_token_transfers', 'erc721_token_transfers', 'erc1155_token_transfers']))

        self._item_exporter.export_items(items)

    @staticmethod
    def _get_exist_token(db_service):
        session = db_service.get_service_session()
        try:
            result = session.query(Tokens.address, Tokens.token_type).all()
            history_token = {}
            if result is not None:
                for item in result:
                    history_token[item[0].hex()] = item[1]
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()
        return history_token

    def _build_rpc_method_data(self, tokens, fn):
        parameters = []

        for token in tokens:
            token_type = token['token_type'] if token['token_type'] is not None else "ELSE"
            try:
                token['param_to'] = token['address']
                token['param_data'] = (self._web3.eth
                                       .contract(address=Web3.to_checksum_address(token['address']),
                                                 abi=erc_token_abi[token_type])
                                       .encodeABI(fn_name=fn))
                for abi_fn in erc_token_abi[token_type]:
                    if fn == abi_fn['name']:
                        token['data_type'] = abi_fn['outputs'][0]['type']

            except Web3ValidationError:
                token['data'] = '0x'
                token['data_type'] = ''
            parameters.append(token)

        return parameters

    def _fetch_token_info(self, tokens):
        fn_names = ['name', 'symbol', 'decimals', 'totalSupply', 'tokenSupply']

        for fn_name in fn_names:
            token_name_rpc = list(generate_eth_call_json_rpc(self._build_rpc_method_data(tokens, fn_name)))
            response = self._batch_web3_provider.make_batch_request(json.dumps(token_name_rpc))
            for data in list(zip(response, tokens)):
                result = rpc_response_to_result(data[0], ignore_errors=True)

                token = data[1]
                token['item'] = 'token'
                value = result[2:] if result is not None else None
                try:
                    token[fn_name] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                    if token['data_type'] == 'string':
                        token[fn_name] = token[fn_name].replace('\u0000', '')
                except Exception as e:
                    token[fn_name] = None

        return tokens
