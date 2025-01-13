import logging
from dataclasses import dataclass
from typing import List, Optional, Union

from eth_utils import to_hex
from hexbytes import HexBytes

from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera.indexer.domains import dict_to_dataclass
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.token import MarkBalanceToken
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseExportJob
from hemera.indexer.utils.abi import pad_address, uint256_to_bytes
from hemera.indexer.utils.abi_setting import ERC20_BALANCE_OF_FUNCTION, ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION
from hemera.indexer.utils.collection_utils import distinct_collections_by_group
from hemera.indexer.utils.exception_recorder import ExceptionRecorder
from hemera.indexer.utils.multicall_hemera.util import calculate_execution_time
from hemera.indexer.utils.token_fetcher import TokenFetcher

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


FAILURE_THRESHOLD = 10


# Exports token balance
class ExportTokenBalancesJob(BaseExportJob):
    dependency_types = [ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [TokenBalance, CurrentTokenBalance, MarkBalanceToken]
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
        parameters = self.extract_token_parameters(token_transfers)
        self._collect_batch(parameters)

    @calculate_execution_time
    def _collect_batch(self, parameters):
        token_balances = self.token_fetcher.fetch_token_balance(parameters)
        results = []
        tokens_set = set()
        for tb in token_balances:
            if tb["balance"] is None and tb["token_address"] in self.tokens:
                self.tokens[tb["token_address"]]["fail_balance_of_count"] += 1
                tokens_set.add(tb["token_address"])
            results.append(dict_to_dataclass(tb, TokenBalance))
        self._collect_items(TokenBalance.type(), results)
        for tk in tokens_set:
            if self.tokens[tk]["fail_balance_of_count"] > FAILURE_THRESHOLD:
                self.tokens[tk]["no_balance_of"] = True
            self._collect_item(
                MarkBalanceToken.type(),
                MarkBalanceToken(
                    address=tk,
                    no_balance_of=self.tokens[tk]["no_balance_of"],
                    fail_balance_of_count=self.tokens[tk]["fail_balance_of_count"],
                ),
            )

    def _process(self, **kwargs):
        if TokenBalance.type() in self._data_buff:
            self._data_buff[TokenBalance.type()].sort(key=lambda x: (x.block_number, x.address))
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
                        for token_balance in self._data_buff[TokenBalance.type()]
                    ],
                    group_by=["token_address", "address", "token_id"],
                    max_key="block_number",
                )
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

    @calculate_execution_time
    def extract_token_parameters(
        self,
        token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]],
        block_number: Union[Optional[int], str] = None,
    ):
        origin_parameters = set()
        token_parameters = []
        for transfer in token_transfers:
            if transfer.token_address in self.tokens and self.tokens[transfer.token_address]["no_balance_of"]:
                continue
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
                    "param_data": encode_balance_abi_parameter(
                        parameter.address, parameter.token_type, parameter.token_id
                    ),
                    "param_number": parameter.block_number if block_number is None else block_number,
                    "block_number": parameter.block_number if block_number is None else block_number,
                    "block_timestamp": parameter.block_timestamp,
                }
            )

        return token_parameters


def encode_balance_abi_parameter(address, token_type, token_id):
    if token_type == "ERC1155":
        encoded_arguments = HexBytes(pad_address(address) + uint256_to_bytes(token_id))
        return to_hex(HexBytes(ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION.get_signature()) + encoded_arguments)
    else:
        encoded_arguments = HexBytes(pad_address(address))
        return to_hex(HexBytes(ERC20_BALANCE_OF_FUNCTION.get_signature()) + encoded_arguments)


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
                "block_number": parameter.block_number if block_number is None else block_number,
                "block_timestamp": parameter.block_timestamp,
            }
        )

    return token_parameters
