import json
import logging
from typing import List

from eth_abi import abi
from web3 import Web3

from indexer.domain.log import Log
from indexer.domain.token import format_token_data
from indexer.domain.token_transfer import extract_transfer_from_log, \
    format_erc20_token_transfer_data, format_erc721_token_transfer_data, format_erc1155_token_transfer_data
from enumeration.entity_type import EntityType
from enumeration.token_type import TokenType
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from common.models.tokens import Tokens
from indexer.jobs.base_job import BaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
erc_token_abi = [
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
    }
]


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
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter
        self._exist_token = get_exist_token(service)

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(
            self._data_buff['log'],
            self._extract_batch,
            total_items=len(self._data_buff['log'])
        )

        self._batch_work_executor.wait()

        tokens = distinct_tokens(self._exist_token, self._data_buff['token'])
        self._data_buff['token'] = []

        self._batch_work_executor.execute(
            tokens,
            self._collect_batch,
            total_items=len(tokens)
        )

        self._batch_work_executor.shutdown()

    def _extract_batch(self, logs):
        tokens, token_transfers = extract_tokens_and_token_transfers(logs)

        for token in tokens:
            token['item'] = 'token'
            self._collect_item(token)

        for transfer_event in token_transfers:
            transfer_event['item'] = 'token_transfer'
            self._collect_item(transfer_event)

    def _collect_batch(self, tokens):

        tokens_info = tokens_rpc_requests(self._web3,
                                          self._batch_web3_provider.make_request,
                                          tokens,
                                          self._is_batch)

        for token in tokens_info:
            token['item'] = 'token'
            self._collect_item(token)

    def _process(self):
        self._data_buff['formated_token'] = [format_token_data(token) for token in self._data_buff['token']]

        (self._data_buff['erc20_token_transfers'],
         self._data_buff['erc721_token_transfers'],
         self._data_buff['erc1155_token_transfers']) = split_token_transfers(self._data_buff['token_transfer'])

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


def get_exist_token(db_service):
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


def extract_tokens_and_token_transfers(logs: List[Log]):
    tokens, token_transfer = [], []
    for log in logs:
        transfer_event = extract_transfer_from_log(log)
        if transfer_event is not None:
            if type(transfer_event) is list:
                token_transfer.extend(transfer_event)

                for event in transfer_event:
                    tokens.append({
                        "address": event['tokenAddress'],
                        "token_type": event['tokenType'],
                        "block_number": event['blockNumber'],
                    })

            else:
                token_transfer.append(transfer_event)

                tokens.append({
                    "address": transfer_event['tokenAddress'],
                    "token_type": transfer_event['tokenType'],
                    "block_number": transfer_event['blockNumber'],
                })

    return tokens, token_transfer


def distinct_tokens(exist_tokens, origin_tokens):
    tokens = dict()
    for token in origin_tokens:
        if token['address'] not in tokens.keys():
            tokens[token['address']] = {
                'token_type': token['token_type'],
                'block_number': token['block_number'],
            }
        elif tokens[token['address']]['block_number'] < token['block_number']:
            tokens[token['address']]['block_number'] = token['block_number']

    tokens_info = []

    for token_address in tokens.keys():
        is_new = True
        if token_address[2:] in exist_tokens.keys():
            is_new = False

        tokens_info.append({
            "address": token_address,
            "token_type": tokens[token_address]['token_type'],
            "block_number": tokens[token_address]['block_number'],
            "request_id": len(tokens_info),
            "is_new": is_new
        })

    return tokens_info


def build_rpc_method_data(web3, tokens, fn, require_new):
    parameters = []

    for token in tokens:

        if not token['is_new'] and require_new:
            continue

        token['param_to'] = token['address']
        token['param_data'] = '0x'
        token['param_number'] = hex(token['block_number'])
        token['data_type'] = ''

        try:
            token['param_data'] = (web3.eth
                                   .contract(address=Web3.to_checksum_address(token['address']),
                                             abi=erc_token_abi)
                                   .encodeABI(fn_name=fn))
            for abi_fn in erc_token_abi:
                if fn == abi_fn['name']:
                    token['data_type'] = abi_fn['outputs'][0]['type']

        except Exception as e:
            logger.warning(
                f"Encoding token abi parameter failed. "
                f"token: {token}. "
                f"fn: {fn}. "
                f"exception: {e}")

        parameters.append(token)

    return parameters


def tokens_rpc_requests(web3, make_requests, tokens, is_batch):
    # if the value of fn is True, then only new token should call fn rpc
    # if the value of fn is False, means every token should call fn rpc
    fn_names = {'name': True, 'symbol': True, 'decimals': True, 'totalSupply': False}

    for fn_name in fn_names.keys():

        token_name_rpc = list(
            generate_eth_call_json_rpc(build_rpc_method_data(web3, tokens, fn_name, fn_names[fn_name])))

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
                token[fn_name] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                if token['data_type'] == 'string':
                    token[fn_name] = token[fn_name].replace('\u0000', '')
            except Exception as e:
                logger.warning(f"Decoding token {fn_name} failed. "
                               f"token: {token}. "
                               f"rpc response: {result}. "
                               f"exception: {e}")
                token[fn_name] = None

    return tokens


def split_token_transfers(token_transfers):
    erc20_token_transfers = []
    erc721_token_transfers = []
    erc1155_token_transfers = []

    for token_transfer in token_transfers:
        if token_transfer['tokenType'] == TokenType.ERC20.value:
            erc20_token_transfers.append(format_erc20_token_transfer_data(token_transfer))
        elif token_transfer['tokenType'] == TokenType.ERC721.value:
            erc721_token_transfers.append(format_erc721_token_transfer_data(token_transfer))
        elif token_transfer['tokenType'] == TokenType.ERC1155.value:
            erc1155_token_transfers.append(format_erc1155_token_transfer_data(token_transfer))

    return erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers
