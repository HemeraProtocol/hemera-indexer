import json
import logging
from typing import List

from eth_abi import abi
from web3 import Web3

from common.utils.format_utils import to_snake_case
from indexer.domain import dict_to_dataclass
from indexer.domain.log import Log
from indexer.domain.token import Token, UpdateToken
from indexer.domain.token_transfer import extract_transfer_from_log, \
    ERC20TokenTransfer, ERC1155TokenTransfer, ERC721TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
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
    output_transfer_types = [ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]
    output_token_types = [Token, UpdateToken]

    dependency_types = [Log]
    output_types = output_transfer_types + output_token_types

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__
        )

        self._is_batch = kwargs['batch_size'] > 1
        self._exist_token = {}
        self._token_params = []

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        self._batch_work_executor.execute(
            self._data_buff[Log.type()],
            self._extract_batch,
            total_items=len(self._data_buff[Log.type()])
        )

        self._batch_work_executor.wait()

        tokens = distinct_tokens(self._exist_token, self._token_params)

        self._batch_work_executor.execute(
            tokens,
            self._collect_batch,
            total_items=len(tokens)
        )

        self._batch_work_executor.shutdown()

    def _extract_batch(self, logs):
        tokens, token_transfers = extract_tokens_and_token_transfers(logs)

        for token in tokens:
            self._token_params.append(token)

        for transfer_event in token_transfers:
            self._collect_item(transfer_event.type(), transfer_event)

    def _collect_batch(self, tokens):

        tokens_info = tokens_rpc_requests(self._web3,
                                          self._batch_web3_provider.make_request,
                                          tokens,
                                          self._is_batch)

        for token in tokens_info:
            if token['is_new']:
                self._collect_item(Token.type(), dict_to_dataclass(token, Token))
            else:
                self._collect_item(UpdateToken.type(), dict_to_dataclass(token, UpdateToken))

    def _process(self):
        for token_transfer_type in self.output_transfer_types:
            if token_transfer_type in self._data_buff:
                self._data_buff[token_transfer_type.type()].sort(
                    key=lambda x: (x.block_number, x.transaction_hash, x.log_index))



def extract_tokens_and_token_transfers(logs: List[Log]):
    tokens, token_transfer = [], []
    for log in logs:
        transfer_events = extract_transfer_from_log(log)

        for transfer_event in transfer_events:
            token_transfer.append(transfer_event)
            tokens.append({
                "address": transfer_event.token_address,
                "token_type": transfer_event.token_type,
                "block_number": transfer_event.block_number,
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
            result = rpc_response_to_result(data[1])

            token = data[0]
            value = result[2:] if result is not None else None
            key = to_snake_case(fn_name)
            try:
                token[key] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                if token['data_type'] == 'string':
                    token[key] = token[fn_name].replace('\u0000', '')
            except Exception as e:
                logger.warning(f"Decoding token {fn_name} failed. "
                               f"token: {token}. "
                               f"rpc response: {result}. "
                               f"exception: {e}")
                token[key] = None

    return tokens
