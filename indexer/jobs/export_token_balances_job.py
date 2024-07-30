import json
import logging
from dataclasses import dataclass
from typing import List, Union, Optional

from eth_abi import abi

from indexer.domain import dict_to_dataclass
from indexer.domain.token_balance import TokenBalance
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.modules.bridge.signature import function_abi_to_4byte_selector_str
from indexer.utils.abi import encode_abi
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response, distinct_collections_by_group, ZERO_ADDRESS

logger = logging.getLogger(__name__)

BALANCE_OF_ABI_FUNCTION = {
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

BALANCE_OF_WITH_TOKEN_ID_ABI_FUNCTION = {
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

balance_of_sig_prefix = function_abi_to_4byte_selector_str(BALANCE_OF_ABI_FUNCTION)
balance_of_token_id_sig_prefix = function_abi_to_4byte_selector_str(BALANCE_OF_WITH_TOKEN_ID_ABI_FUNCTION)


@dataclass(frozen=True)
class TokenBalanceParam:
    address: str
    token_address: str
    token_id: Optional[int]
    token_type: str
    block_number: int
    block_timestamp: int


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
        parameters = extract_token_parameters(token_transfers)

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
                [CurrentTokenBalance(
                    address=token_balance.address,
                    token_id=token_balance.token_id,
                    token_type=token_balance.token_type,
                    token_address=token_balance.token_address,
                    balance=token_balance.balance,
                    block_number=token_balance.block_number,
                    block_timestamp=token_balance.block_timestamp)
                    for token_balance in self._data_buff[TokenBalance.type()]],
                group_by=['token_address', 'address'],
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


def encode_balance_abi_parameter(address, token_type, token_id):
    if token_type == 'ERC1155':
        return encode_abi(BALANCE_OF_WITH_TOKEN_ID_ABI_FUNCTION, [address, token_id], balance_of_token_id_sig_prefix)
    else:
        return encode_abi(BALANCE_OF_ABI_FUNCTION, [address], balance_of_sig_prefix)


def extract_token_parameters(
        token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]]):
    origin_parameters = set()
    token_parameters = []
    for transfer in token_transfers:
        common_params = {
            'token_address': transfer.token_address,
            'token_id': transfer.token_id if isinstance(transfer, ERC1155TokenTransfer) else None,
            'token_type': transfer.token_type,
            'block_number': transfer.block_number,
            'block_timestamp': transfer.block_timestamp
        }
        if transfer.from_address != ZERO_ADDRESS:
            origin_parameters.add(TokenBalanceParam(address=transfer.from_address, **common_params))
        if transfer.to_address != ZERO_ADDRESS:
            origin_parameters.add(TokenBalanceParam(address=transfer.to_address, **common_params))

    for parameter in origin_parameters:
        token_parameters.append({
            'address': parameter.address,
            'token_address': parameter.token_address,
            'token_id': parameter.token_id,
            'token_type': parameter.token_type,
            'param_to': parameter.token_address,
            'param_data': encode_balance_abi_parameter(parameter.address, parameter.token_type, parameter.token_id),
            'param_number': hex(parameter.block_number),
            'block_number': parameter.block_number,
            'block_timestamp': parameter.block_timestamp,
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
