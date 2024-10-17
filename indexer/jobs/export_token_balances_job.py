import logging
from dataclasses import dataclass
from typing import List, Optional, Union

from eth_utils import to_hex
from hexbytes import HexBytes

from common.utils.web3_utils import ZERO_ADDRESS
from indexer.domain import dict_to_dataclass
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.utils.abi import pad_address, uint256_to_bytes
from indexer.utils.abi_setting import ERC20_BALANCE_OF_FUNCTION, ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION
from indexer.utils.collection_utils import distinct_collections_by_group
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.token_fetcher import TokenFetcher

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()


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
        self._is_multi_call = kwargs["multicall"]
        self.token_fetcher = TokenFetcher(self._web3, kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        token_transfers = self._collect_all_token_transfers()
        parameters = extract_token_parameters(token_transfers)
        if self._is_multi_call:
            self._collect_batch(parameters)
        else:
            self._batch_work_executor.execute(parameters, self._collect_batch, total_items=len(parameters))
            self._batch_work_executor.wait()

    @calculate_execution_time
    def _collect_batch(self, parameters):
        token_balances = self.token_fetcher.fetch_token_balance(parameters)
        results = [dict_to_dataclass(t, TokenBalance) for t in token_balances]
        self._collect_items(TokenBalance.type(), results)

    def _process(self, **kwargs):
        if TokenBalance.type() in self.output_collection:
            self.output_collection[TokenBalance.type()].sort(key=lambda x: (x.block_number, x.address))
            self._update_domains(
                distinct_collections_by_group(
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
                        for token_balance in self.output_collection[TokenBalance.type()]
                    ],
                    group_by=["token_address", "address", "token_id"],
                    max_key="block_number",
                )
            )

    @calculate_execution_time
    def _collect_all_token_transfers(self):
        token_transfers = []
        if ERC20TokenTransfer.type() in self.dependency_collection:
            token_transfers += self.dependency_collection[ERC20TokenTransfer.type()]

        if ERC721TokenTransfer.type() in self.dependency_collection:
            token_transfers += self.dependency_collection[ERC721TokenTransfer.type()]

        if ERC1155TokenTransfer.type() in self.dependency_collection:
            token_transfers += self.dependency_collection[ERC1155TokenTransfer.type()]

        return token_transfers


def encode_balance_abi_parameter(address, token_type, token_id):
    if token_type == "ERC1155":
        encoded_arguments = HexBytes(pad_address(address) + uint256_to_bytes(token_id))
        return to_hex(HexBytes(ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION.get_signature()) + encoded_arguments)
    else:
        encoded_arguments = HexBytes(pad_address(address))
        return to_hex(HexBytes(ERC20_BALANCE_OF_FUNCTION.get_signature()) + encoded_arguments)


@calculate_execution_time
def extract_token_parameters(
    token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]],
    block_number: Union[Optional[int], str] = None,
):
    origin_parameters = set()
    token_parameters = []
    for transfer in token_transfers:
        common_params = {
            "token_address": transfer.token_address,
            "token_id": (transfer.token_id if isinstance(transfer, ERC1155TokenTransfer) else None),
            "token_type": transfer.token_type,
            "block_number": transfer.block_number if block_number is None else block_number,
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
                "param_number": parameter.block_number if block_number is None else block_number,
                "block_number": parameter.block_number if block_number is None else None,
                "block_timestamp": parameter.block_timestamp,
            }
        )

    return token_parameters
