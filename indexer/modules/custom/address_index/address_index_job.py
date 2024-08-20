import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

from eth_abi import abi

from indexer.domain import dict_to_dataclass
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.jobs.export_token_balances_job import BALANCE_OF_ABI_FUNCTION
from indexer.jobs.export_tokens_and_transfers_job import OWNER_OF_ABI_FUNCTION
from indexer.modules.custom.address_index.domain.address_nft_transfer import AddressNftTransfer
from indexer.modules.custom.address_index.domain.address_token_holder import AddressTokenHolder
from indexer.modules.custom.address_index.domain.address_token_transfer import AddressTokenTransfer
from indexer.modules.custom.address_index.domain.address_transaction import AddressTransaction
from indexer.modules.custom.address_index.domain.token_address_nft_inventory import TokenAddressNftInventory
from indexer.utils.abi import encode_abi, function_abi_to_4byte_selector_str
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc_without_block_number, generate_json_rpc
from indexer.utils.utils import ZERO_ADDRESS, rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)


class AddressTransactionType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    CREATOR = 3
    BEEN_CREATED = 4


class AddressTokenTransferType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    DEPOSITOR = 3
    WITHDRAWER = 4


class AddressNftTransferType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    BURNER = 3
    MINTER = 4


def create_address_transaction(transaction, address, txn_type, the_other_address, transaction_fee):
    return AddressTransaction(
        address=address,
        block_number=transaction.block_number,
        transaction_index=transaction.transaction_index,
        transaction_hash=transaction.hash,
        block_timestamp=transaction.block_timestamp,
        block_hash=transaction.block_hash,
        txn_type=txn_type,
        the_other_address=the_other_address,
        value=transaction.value,
        transaction_fee=transaction_fee,
        receipt_status=transaction.receipt.status,
        method=transaction.input[2:10],
    )


def transactions_to_address_transactions(transactions: List[Transaction]):
    for transaction in transactions:
        transaction_fee = transaction.receipt.gas_used * transaction.gas_price + (transaction.receipt.l1_fee or 0)
        assert transaction.from_address is not None
        assert transaction.to_address is not None or transaction.receipt.contract_address is not None

        if transaction.from_address != transaction.to_address:
            if transaction.to_address is not None:
                yield create_address_transaction(
                    transaction,
                    transaction.to_address,
                    AddressTransactionType.RECEIVER.value,
                    transaction.from_address,
                    transaction_fee,
                )
                yield create_address_transaction(
                    transaction,
                    transaction.from_address,
                    AddressTransactionType.SENDER.value,
                    transaction.to_address,
                    transaction_fee,
                )
            else:
                yield create_address_transaction(
                    transaction,
                    transaction.receipt.contract_address,
                    AddressTransactionType.BEEN_CREATED.value,
                    transaction.from_address,
                    transaction_fee,
                )
                yield create_address_transaction(
                    transaction,
                    transaction.from_address,
                    AddressTransactionType.CREATOR.value,
                    transaction.receipt.contract_address,
                    transaction_fee,
                )
        else:
            yield create_address_transaction(
                transaction,
                transaction.from_address,
                AddressTransactionType.SELF_CALL.value,
                transaction.from_address,
                transaction_fee,
            )


def create_address_token_transfer(token_transfer: ERC20TokenTransfer, address, transfer_type, the_other_address):
    return AddressTokenTransfer(
        address=address,
        block_number=token_transfer.block_number,
        log_index=token_transfer.log_index,
        transaction_hash=token_transfer.transaction_hash,
        block_timestamp=token_transfer.block_timestamp,
        block_hash=token_transfer.block_hash,
        token_address=token_transfer.token_address,
        the_other_address=the_other_address,
        transfer_type=transfer_type,
        value=token_transfer.value,
    )


def erc20_transfers_to_address_token_transfers(transfers: List[ERC20TokenTransfer]):
    for transfer in transfers:
        assert transfer.from_address is not None
        assert transfer.to_address is not None

        if transfer.from_address != transfer.to_address:
            if transfer.from_address == ZERO_ADDRESS:
                yield create_address_token_transfer(
                    transfer, transfer.to_address, AddressTokenTransferType.WITHDRAWER.value, transfer.from_address
                )
            elif transfer.to_address == ZERO_ADDRESS:
                yield create_address_token_transfer(
                    transfer, transfer.from_address, AddressTokenTransferType.DEPOSITOR.value, transfer.to_address
                )
            else:
                yield create_address_token_transfer(
                    transfer, transfer.to_address, AddressTokenTransferType.RECEIVER.value, transfer.from_address
                )
                yield create_address_token_transfer(
                    transfer, transfer.from_address, AddressTokenTransferType.SENDER.value, transfer.to_address
                )
        else:
            yield create_address_token_transfer(
                transfer, transfer.from_address, AddressTokenTransferType.SELF_CALL.value, transfer.from_address
            )


def create_address_nft_transfer(nft_transfer: ERC721TokenTransfer, address, transfer_type, the_other_address):
    return AddressNftTransfer(
        address=address,
        block_number=nft_transfer.block_number,
        log_index=nft_transfer.log_index,
        transaction_hash=nft_transfer.transaction_hash,
        block_timestamp=nft_transfer.block_timestamp,
        block_hash=nft_transfer.block_hash,
        token_address=nft_transfer.token_address,
        the_other_address=the_other_address,
        transfer_type=transfer_type,
        token_id=nft_transfer.token_id,
    )


def erc721_transfers_to_address_nft_transfers(transfers: List[ERC721TokenTransfer]):
    for transfer in transfers:
        assert transfer.from_address is not None
        assert transfer.to_address is not None

        if transfer.from_address != transfer.to_address:
            if transfer.from_address == ZERO_ADDRESS:
                yield create_address_nft_transfer(
                    transfer, transfer.to_address, AddressNftTransferType.MINTER.value, transfer.from_address
                )
            elif transfer.to_address == ZERO_ADDRESS:
                yield create_address_nft_transfer(
                    transfer, transfer.from_address, AddressNftTransferType.BURNER.value, transfer.to_address
                )
            else:
                yield create_address_nft_transfer(
                    transfer, transfer.to_address, AddressNftTransferType.RECEIVER.value, transfer.from_address
                )
                yield create_address_nft_transfer(
                    transfer, transfer.from_address, AddressNftTransferType.SENDER.value, transfer.to_address
                )
        else:
            yield create_address_nft_transfer(
                transfer, transfer.from_address, AddressNftTransferType.SELF_CALL.value, transfer.from_address
            )


balance_of_sig_prefix = function_abi_to_4byte_selector_str(BALANCE_OF_ABI_FUNCTION)
owner_of_sig_prefix = function_abi_to_4byte_selector_str(OWNER_OF_ABI_FUNCTION)


def encode_balance_abi_parameter(address):
    return encode_abi(BALANCE_OF_ABI_FUNCTION, [address], balance_of_sig_prefix)


def encode_owner_of_abi_parameter(token_id):
    return encode_abi(OWNER_OF_ABI_FUNCTION, [token_id], owner_of_sig_prefix)


@dataclass(frozen=True)
class TokenBalanceParam:
    address: str
    token_address: str


@dataclass(frozen=True)
class TokenOwnerParam:
    token_address: str
    token_id: int


def extract_token_parameters(token_transfers: List[Union[ERC20TokenTransfer, ERC721TokenTransfer]]):
    origin_parameters = set()
    token_parameters = []
    for transfer in token_transfers:
        if transfer.from_address != ZERO_ADDRESS:
            origin_parameters.add(
                TokenBalanceParam(address=transfer.from_address, token_address=transfer.token_address)
            )
        if transfer.to_address != ZERO_ADDRESS:
            origin_parameters.add(TokenBalanceParam(address=transfer.to_address, token_address=transfer.token_address))

    for parameter in origin_parameters:
        token_parameters.append(
            {
                "address": parameter.address,
                "token_address": parameter.token_address,
                "param_to": parameter.token_address,
                "param_data": encode_balance_abi_parameter(parameter.address),
            }
        )

    return token_parameters


def extract_nft_owner_parameters(nft_transfers: List[ERC721TokenTransfer]):
    origin_parameters = set()
    token_parameters = []
    for transfer in nft_transfers:
        origin_parameters.add(TokenOwnerParam(token_address=transfer.token_address, token_id=transfer.token_id))

    for parameter in origin_parameters:
        token_parameters.append(
            {
                "token_address": parameter.token_address,
                "token_id": parameter.token_id,
                "param_to": parameter.token_address,
                "param_data": encode_owner_of_abi_parameter(parameter.token_id),
            }
        )

    return token_parameters


class AddressIndexerJob(BaseJob):
    dependency_types = [Transaction, ERC20TokenTransfer, ERC721TokenTransfer]
    output_types = [
        TokenAddressNftInventory,
        AddressTransaction,
        AddressTokenTransfer,
        AddressNftTransfer,
        AddressTokenHolder,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        erc20_transfers = self._get_domain(ERC20TokenTransfer)
        erc721_transfers = self._get_domain(ERC721TokenTransfer)
        token_transfers = erc20_transfers + erc721_transfers
        parameters = extract_token_parameters(token_transfers)

        self._batch_work_executor.execute(parameters, self._export_token_balances_batch, total_items=len(parameters))
        self._batch_work_executor.wait()

        parameters = extract_nft_owner_parameters(erc721_transfers)

        self._batch_work_executor.execute(parameters, self._export_token_owner_batch, total_items=len(parameters))
        self._batch_work_executor.wait()

    def _export_token_owner_batch(self, parameters):
        token_balances = token_owner_rpc_requests(self._batch_web3_provider.make_request, parameters, self._is_batch)
        for token_balance in token_balances:
            self._collect_domain(dict_to_dataclass(token_balance, TokenAddressNftInventory))

    def _export_token_balances_batch(self, parameters):
        token_balances = token_balances_rpc_requests(self._batch_web3_provider.make_request, parameters, self._is_batch)
        for token_balance in token_balances:
            self._collect_domain(dict_to_dataclass(token_balance, AddressTokenHolder))

    def _process(self, **kwargs):
        transactions = self._get_domain(Transaction)
        self._collect_domains(list(transactions_to_address_transactions(transactions)))

        token_transfers = self._get_domain(ERC20TokenTransfer)
        self._collect_domains(list(erc20_transfers_to_address_token_transfers(token_transfers)))

        nft_transfers = self._get_domain(ERC721TokenTransfer)
        self._collect_domains(list(erc721_transfers_to_address_nft_transfers(nft_transfers)))


def token_owner_rpc_requests(make_requests, tokens, is_batch):
    for idx, token in enumerate(tokens):
        token["request_id"] = idx

    token_balance_rpc = list(generate_eth_call_json_rpc_without_block_number(tokens))

    if is_batch:
        response = make_requests(params=json.dumps(token_balance_rpc))
    else:
        response = [make_requests(params=json.dumps(token_balance_rpc[0]))]

    token_owners = []
    for data in list(zip_rpc_response(tokens, response)):
        result = rpc_response_to_result(data[1])
        wallet_address = None

        try:
            if result:
                wallet_address = abi.decode(["address"], bytes.fromhex(result[2:]))[0]
        except Exception as e:
            logger.warning(f"Decoding token balance value failed. " f"rpc response: {result}. " f"exception: {e}. ")

        token_owners.append(
            {
                "token_id": data[0]["token_id"],
                "token_address": data[0]["token_address"].lower(),
                "wallet_address": wallet_address,
            }
        )

    return token_owners


def token_balances_rpc_requests(make_requests, tokens, is_batch):
    for idx, token in enumerate(tokens):
        token["request_id"] = idx

    token_balance_rpc = list(generate_eth_call_json_rpc_without_block_number(tokens))

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
                balance = abi.decode(["uint256"], bytes.fromhex(result[2:]))[0]
        except Exception as e:
            logger.warning(f"Decoding token balance value failed. " f"rpc response: {result}. " f"exception: {e}. ")

        token_balances.append(
            {
                "address": data[0]["address"].lower(),
                "token_address": data[0]["token_address"].lower(),
                "balance_of": balance,
            }
        )

    return token_balances
