import json
import logging
from enum import Enum
from itertools import groupby
from typing import List, Union

from eth_abi import abi

from indexer.domain.token_id_infos import UpdateERC721TokenIdDetail
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob
from indexer.jobs.export_token_balances_job import extract_token_parameters
from indexer.jobs.export_token_id_infos_job import generate_token_id_info
from indexer.modules.custom.address_index.domain.address_nft_1155_holders import AddressNft1155Holder
from indexer.modules.custom.address_index.domain.address_nft_transfer import AddressNftTransfer
from indexer.modules.custom.address_index.domain.address_token_holder import AddressTokenHolder
from indexer.modules.custom.address_index.domain.address_token_transfer import AddressTokenTransfer
from indexer.modules.custom.address_index.domain.address_transaction import AddressTransaction
from indexer.modules.custom.address_index.domain.token_address_nft_inventory import TokenAddressNftInventory
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc_without_block_number
from indexer.utils.token_fetcher import TokenFetcher
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


def create_address_transaction(transaction, address, txn_type, related_address, transaction_fee):
    return AddressTransaction(
        address=address,
        block_number=transaction.block_number,
        transaction_index=transaction.transaction_index,
        transaction_hash=transaction.hash,
        block_timestamp=transaction.block_timestamp,
        block_hash=transaction.block_hash,
        txn_type=txn_type,
        related_address=related_address,
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


def create_address_token_transfer(token_transfer: ERC20TokenTransfer, address, transfer_type, related_address):
    return AddressTokenTransfer(
        address=address,
        block_number=token_transfer.block_number,
        log_index=token_transfer.log_index,
        transaction_hash=token_transfer.transaction_hash,
        block_timestamp=token_transfer.block_timestamp,
        block_hash=token_transfer.block_hash,
        token_address=token_transfer.token_address,
        related_address=related_address,
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


def create_address_nft_transfer(
    nft_transfer: Union[ERC721TokenTransfer, ERC1155TokenTransfer], address, transfer_type, related_address
):
    return AddressNftTransfer(
        address=address,
        block_number=nft_transfer.block_number,
        log_index=nft_transfer.log_index,
        transaction_hash=nft_transfer.transaction_hash,
        block_timestamp=nft_transfer.block_timestamp,
        block_hash=nft_transfer.block_hash,
        token_address=nft_transfer.token_address,
        related_address=related_address,
        transfer_type=transfer_type,
        token_id=nft_transfer.token_id,
        value=nft_transfer.value if isinstance(nft_transfer, ERC1155TokenTransfer) else 1,
    )


def nft_transfers_to_address_nft_transfers(transfers: Union[List[ERC721TokenTransfer], List[ERC1155TokenTransfer]]):
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


class AddressIndexerJob(ExtensionJob):
    dependency_types = [Transaction, ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]
    output_types = [
        TokenAddressNftInventory,
        AddressTransaction,
        AddressTokenTransfer,
        AddressNftTransfer,
        AddressTokenHolder,
        AddressNft1155Holder,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self.token_fetcher = TokenFetcher(self._web3, kwargs)
        self._is_multi_call = kwargs["multicall"]

    def _collect_all_token_transfers(self):
        token_transfers = []
        if ERC20TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC20TokenTransfer.type()]

        if ERC721TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC721TokenTransfer.type()]

        if ERC1155TokenTransfer.type() in self._data_buff:
            token_transfers += self._data_buff[ERC1155TokenTransfer.type()]

        return token_transfers

    def _collect(self, **kwargs):
        token_transfers = self._collect_all_token_transfers()

        all_token_parameters = extract_token_parameters(token_transfers, "latest")
        all_token_parameters.sort(key=lambda x: (x["address"], x["token_address"], x["token_id"]))
        parameters = [
            list(group)[-1]
            for key, group in groupby(all_token_parameters, lambda x: (x["address"], x["token_address"]))
        ]

        all_owner_parameters = generate_token_id_info(self._data_buff[ERC721TokenTransfer.type()], [], "latest")
        all_owner_parameters.sort(key=lambda x: (x["address"], x["token_id"]))
        owner_parameters = [
            list(group)[-1] for key, group in groupby(all_owner_parameters, lambda x: (x["address"], x["token_id"]))
        ]

        if self._is_multi_call:
            self._collect_balance_batch(parameters)
            self._collect_owner_batch(owner_parameters)
        else:
            self._batch_work_executor.execute(parameters, self._collect_balance_batch, total_items=len(parameters))
            self._batch_work_executor.wait()
            self._batch_work_executor.execute(
                owner_parameters, self._collect_owner_batch, total_items=len(owner_parameters)
            )
            self._batch_work_executor.wait()

    def _collect_owner_batch(self, token_list):
        items = self.token_fetcher.fetch_token_ids_info(token_list)
        update_erc721_token_id_details = []
        for item in items:
            if item.type() == UpdateERC721TokenIdDetail.type():
                update_erc721_token_id_details.append(item)

        update_erc721_token_id_details = [
            list(group)[-1]
            for key, group in groupby(
                update_erc721_token_id_details,
                lambda x: (x.token_address, x.token_id),
            )
        ]

        for item in update_erc721_token_id_details:
            self._collect_domain(
                TokenAddressNftInventory(
                    token_address=item.token_address, token_id=item.token_id, wallet_address=item.token_owner
                )
            )

    def _collect_balance_batch(self, parameters):
        token_balances = self.token_fetcher.fetch_token_balance(parameters)
        token_balances.sort(key=lambda x: (x["address"], x["token_address"]))
        for token_balance in token_balances:
            if token_balance["token_type"] == "ERC1155":
                self._collect_domain(
                    AddressNft1155Holder(
                        address=token_balance["address"],
                        token_address=token_balance["token_address"],
                        token_id=token_balance["token_id"],
                        balance_of=token_balance["balance"],
                    )
                )
            else:
                self._collect_domain(
                    AddressTokenHolder(
                        address=token_balance["address"],
                        token_address=token_balance["token_address"],
                        balance_of=token_balance["balance"],
                    )
                )

    def _process(self, **kwargs):
        transactions = self._get_domain(Transaction)
        self._collect_domains(list(transactions_to_address_transactions(transactions)))

        token_transfers = self._get_domain(ERC20TokenTransfer)
        self._collect_domains(list(erc20_transfers_to_address_token_transfers(token_transfers)))

        nft_transfers = self._get_domain(ERC721TokenTransfer)
        self._collect_domains(list(nft_transfers_to_address_nft_transfers(nft_transfers)))

        erc1155_transfers = self._get_domain(ERC1155TokenTransfer)
        self._collect_domains(list(nft_transfers_to_address_nft_transfers(erc1155_transfers)))


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
