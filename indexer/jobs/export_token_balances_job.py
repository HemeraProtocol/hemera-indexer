import logging
import os
from dataclasses import dataclass
from functools import partial
from typing import List, Optional, Union

from mpire import WorkerPool
from eth_abi import abi
from eth_utils import to_hex
from hexbytes import HexBytes

from indexer.domain import dict_to_dataclass
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.modules.bridge.signature import function_abi_to_4byte_selector_str
from indexer.utils.abi import encode_abi
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.multi_call_util import MultiCallProxy
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS, distinct_collections_by_group

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()

BALANCE_OF_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

BALANCE_OF_WITH_TOKEN_ID_ABI_FUNCTION = {
    "constant": True,
    "inputs": [
        {"name": "account", "type": "address"},
        {"name": "id", "type": "uint256"},
    ],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
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
class ExportTokenBalancesJob(BaseExportJob):
    dependency_types = [ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [TokenBalance, CurrentTokenBalance]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self.multi_call_util = MultiCallProxy(self._web3, kwargs)

    def _start(self):
        super()._start()

    @calculate_execution_time
    def _collect(self, **kwargs):
        token_transfers = self._collect_all_token_transfers()
        parameters = extract_token_parameters(token_transfers)
        self._collect_batch(parameters)

    @calculate_execution_time
    def _collect_batch(self, parameters):
        token_balances = self.multi_call_util.fetch_token_balance(parameters)
        results = self._collect_batch_convert(token_balances)
        self._collect_items(TokenBalance.type(), results)

    @calculate_execution_time
    def _collect_batch_convert(self, token_balances):
        convert = partial(dict_to_dataclass, cls=TokenBalance)
        with WorkerPool(os.cpu_count()) as pool:
            results = pool.map(convert, [(t,) for t in token_balances])
        return results

    def _process(self, **kwargs):
        if TokenBalance.type() in self._data_buff:
            self._data_buff[TokenBalance.type()].sort(key=lambda x: (x.block_number, x.address))

            self._data_buff[CurrentTokenBalance.type()] = distinct_collections_by_group(
                [
                    CurrentTokenBalance(
                        address=token_balance.address,
                        token_id=token_balance.token_id,
                        token_type=token_balance.token_type,
                        token_address=token_balance.token_address,
                        balance=token_balance.balance,
                        block_number=token_balance.block_number,
                        block_timestamp=token_balance.block_timestamp,
                    )
                    for token_balance in self._data_buff[TokenBalance.type()]
                ],
                group_by=["token_address", "address"],
                max_key="block_number",
            )

    @calculate_execution_time
    def _collect_all_token_transfers(self):
        token_transfers = []
        if ERC20TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC20TokenTransfer.type()]

        if ERC721TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC721TokenTransfer.type()]

        if ERC1155TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC1155TokenTransfer.type()]

        return token_transfers


def uint256_to_bytes(value: int) -> bytes:
    if value < 0 or value >= 2**256:
        raise ValueError("Value out of uint256 range")

    return value.to_bytes(32, byteorder="big")


def pad_address(address: str) -> bytes:
    address = address.lower().replace("0x", "")

    if len(address) != 40:
        raise ValueError("Invalid address length")

    padded = "0" * 24 + address
    return bytes.fromhex(padded)


def encode_balance_abi_parameter(address, token_type, token_id):
    if token_type == "ERC1155":
        encoded_arguments = HexBytes(pad_address(address) + uint256_to_bytes(token_id))
        return to_hex(HexBytes(balance_of_token_id_sig_prefix) + encoded_arguments)
    else:
        encoded_arguments = HexBytes((address))
        return to_hex(HexBytes(balance_of_sig_prefix) + encoded_arguments)


@calculate_execution_time
def extract_token_parameters(
    token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]]
):
    origin_parameters = set()
    token_parameters = []
    for transfer in token_transfers:
        common_params = {
            "token_address": transfer.token_address,
            "token_id": (transfer.token_id if isinstance(transfer, ERC1155TokenTransfer) else None),
            "token_type": transfer.token_type,
            "block_number": transfer.block_number,
            "block_timestamp": transfer.block_timestamp,
        }
        if transfer.from_address != ZERO_ADDRESS:
            origin_parameters.add(TokenBalanceParam(address=transfer.from_address, **common_params))
        if transfer.to_address != ZERO_ADDRESS:
            origin_parameters.add(TokenBalanceParam(address=transfer.to_address, **common_params))

    for parameter in origin_parameters:
        token_parameters.append(
            {
                "address": parameter.address,
                "token_address": parameter.token_address,
                "token_id": parameter.token_id,
                "token_type": parameter.token_type,
                "param_to": parameter.token_address,
                "param_data": encode_balance_abi_parameter(parameter.address, parameter.token_type, parameter.token_id),
                "param_number": hex(parameter.block_number),
                "block_number": parameter.block_number,
                "block_timestamp": parameter.block_timestamp,
            }
        )

    return token_parameters
