import json
import logging
from typing import List, Union

import numpy
import pandas
from eth_abi import abi
from web3 import Web3

from indexer.domain import dict_to_dataclass
from indexer.domain.token_balance import TokenBalance, CurrentTokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response, distinct_collections_by_group


def verify_0_address(address):
    return set(address[2:]) == {'0'}


logger = logging.getLogger(__name__)

contract_abi = {
    "ERC20": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "_owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "ERC721": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "ERC1155": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "account",
                    "type": "address"
                },
                {
                    "name": "id",
                    "type": "uint256"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
}


# Exports token balance
class ExportTokenBalancesJob(BaseJob):
    dependency_types = [ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [TokenBalance, CurrentTokenBalance]

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__
        )
        self._is_batch = kwargs['batch_size'] > 1

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):

        token_transfers = self._collect_all_token_transfers()
        parameters = extract_token_parameters(token_transfers, self._web3)

        self._batch_work_executor.execute(parameters,
                                          self._collect_batch,
                                          total_items=len(parameters))
        self._batch_work_executor.wait()

    def _collect_batch(self, parameters):
        token_balances = token_balances_rpc_requests(self._batch_web3_provider.make_request, parameters, self._is_batch)
        for token_balance in token_balances:
            self._collect_item(TokenBalance.type(), dict_to_dataclass(token_balance, TokenBalance))

    def _process(self):
        if TokenBalance.type() in self._data_buff:
            self._data_buff[TokenBalance.type()].sort(key=lambda x: (x.block_number, x.address))

            self._data_buff[CurrentTokenBalance.type()] = distinct_collections_by_group(
                [CurrentTokenBalance.from_token_balance(token_balance)
                 for token_balance in self._data_buff[TokenBalance.type()]],
                group_by=['token_address', 'wallet_address'],
                max_key='block_number')

    def _collect_all_token_transfers(self):
        token_transfers = []
        if ERC20TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC20TokenTransfer.type()]

        if ERC721TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC721TokenTransfer.type()]

        if ERC1155TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC1155TokenTransfer.type()]

        return token_transfers


def extract_token_parameters(
        token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]],
        web3):
    origin_parameters = []

    for transfer in token_transfers:
        from_address = Web3.to_checksum_address(transfer.from_address)
        to_address = Web3.to_checksum_address(transfer.to_address)
        token_address = Web3.to_checksum_address(transfer.token_address)

        origin_parameters.append({
            'address': from_address,
            'token_address': token_address,
            'token_id': transfer.token_id if not isinstance(transfer, ERC20TokenTransfer) else None,
            'token_type': transfer.token_type,
            'block_number': transfer.block_number,
            'block_timestamp': transfer.block_timestamp,
        })
        origin_parameters.append({
            'address': to_address,
            'token_address': token_address,
            'token_id': transfer.token_id if not isinstance(transfer, ERC20TokenTransfer) else None,
            'token_type': transfer.token_type,
            'block_number': transfer.block_number,
            'block_timestamp': transfer.block_timestamp,
        })

    token_parameters = []
    a = pandas.DataFrame(origin_parameters).drop_duplicates().replace(numpy.NaN, None).to_dict(
        orient='records')
    for parameter in a:
        parameter['token_id'] = int(parameter['token_id']) if parameter['token_id'] is not None else None
        if not verify_0_address(parameter['address']):
            contract = web3.eth.contract(address=parameter['token_address'],
                                         abi=contract_abi[parameter['token_type']])
            data = None
            try:
                if len(contract_abi[parameter['token_type']][0]['inputs']) > 1:
                    data = contract.encodeABI(fn_name='balanceOf', args=[parameter['address'], parameter['token_id']])
                else:
                    data = contract.encodeABI(fn_name='balanceOf', args=[parameter['address']])
            except Exception as e:
                logger.warning(f"Encoding token balance api parameter failed. "
                               f"token: {parameter}. "
                               f"fn: balanceOf. "
                               f"exception: {e}. ")

            token_parameters.append({
                'address': parameter['address'],
                'token_address': parameter['token_address'],
                'token_id': parameter['token_id'],
                'token_type': parameter['token_type'],
                'param_to': parameter['token_address'],
                'param_data': data,
                'param_number': hex(parameter['block_number']),
                'block_number': parameter['block_number'],
                'block_timestamp': parameter['block_timestamp'],
            })

    return token_parameters


def token_balances_rpc_requests(make_requests, tokens, is_batch):
    for idx, token in enumerate(tokens):
        token['request_id'] = idx

    token_balance_rpc = list(generate_eth_call_json_rpc(tokens))

    if is_batch:
        response = make_requests(params=json.dumps(token_balance_rpc))
    else:
        response = [make_requests(params=json.dumps(token_balance_rpc[0]))]

    token_balances = []
    for data in list(zip_rpc_response(tokens, response)):
        result = rpc_response_to_result(data[1])
        balance = None

        try:
            if result:
                balance = abi.decode(['uint256'], bytes.fromhex(result[2:]))[0]
        except Exception as e:
            logger.warning(f"Decoding token balance value failed. "
                           f"token address: {data[0]['token_address']}. "
                           f"rpc response: {result}. "
                           f"block number: {data[0]['block_number']}. "
                           f"exception: {e}. ")

        token_balances.append({
            'address': data[0]['address'].lower(),
            'token_id': data[0]['token_id'],
            'token_type': data[0]['token_type'],
            'token_address': data[0]['token_address'].lower(),
            'balance': balance,
            'block_number': data[0]['block_number'],
            'block_timestamp': data[0]['block_timestamp'],
        })

    return token_balances
