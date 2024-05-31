import json

from eth_abi import abi
from eth_abi.exceptions import InsufficientDataBytes
from web3 import Web3

from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_token_info_json_rpc
from utils.utils import rpc_response_to_result, hex_to_dec

erc_abi = {
    "ERC20": [
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
    "ERC721": [
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
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
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
        }
    ],
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
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }

    ]
}


# Exports coin balance
class ExportTokensInfoJob(BaseJob):
    def __init__(
            self,
            token_transfer_iterable,
            except_tokens,
            batch_size,
            batch_web3_provider,
            web3,
            max_workers,
            index_keys):

        self.token_parameter = []

        tokens_set = set()
        for token in token_transfer_iterable:
            if (token['tokenAddress'], token['tokenType']) not in except_tokens:
                tokens_set.add((token['tokenAddress'], token['tokenType']))
        for token in tokens_set:
            self.token_parameter.append(
                {
                    "address": token[0],
                    "token_type": token[1]
                }
            )

        self.batch_web3_provider = batch_web3_provider
        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.web3 = web3
        self.index_keys = index_keys

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.token_parameter, self._export_batch)

    def _export_batch(self, tokens):
        fn_names = ['name', 'symbol', 'totalSupply', 'decimals']

        for fn_names in fn_names:
            token_name_rpc = list(generate_get_token_info_json_rpc(self.build_rpc_method_data(tokens, fn_names)))
            response = self.batch_web3_provider.make_batch_request(json.dumps(token_name_rpc))
            for data in list(zip(response, tokens)):
                result = rpc_response_to_result(data[0], ignore_errors=True)

                token = data[1]
                token['item'] = 'tokens'
                value = result[2:] if result is not None else None
                try:
                    token[fn_names] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                except (InsufficientDataBytes, TypeError) as e:
                    token[fn_names] = None

        for token in tokens:
            self._export_item(token)

    def _end(self):
        self.batch_work_executor.shutdown()

    def build_rpc_method_data(self, tokens, fn):
        parameters = []

        for token in tokens:
            token['data'] = (self.web3.eth
                             .contract(address=Web3.to_checksum_address(token['address']),
                                       abi=erc_abi[token['token_type']])
                             .encodeABI(fn_name=fn))
            for abi_fn in erc_abi[token['token_type']]:
                if fn == abi_fn['name']:
                    token['data_type'] = abi_fn['outputs'][0]['type']
            parameters.append(token)

        return parameters
