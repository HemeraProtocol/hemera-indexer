from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class AddressContractOperation(Domain):
    address: str

    trace_from_address: str
    contract_address: str

    trace_id: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str

    error: str
    status: int

    creation_code: str
    deployed_code: str

    gas: int
    gas_used: int

    trace_type: str
    call_type: str

    transaction_receipt_status: int


@dataclass
class AddressInternalTransaction(Domain):
    address: str

    trace_id: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str

    error: str
    status: int

    input_method: str

    value: int
    gas: int
    gas_used: int

    trace_type: str
    call_type: str

    txn_type: int
    related_address: str

    transaction_receipt_status: int


@dataclass
class AddressNft1155Holder(Domain):
    address: str
    token_address: str
    token_id: int
    balance_of: str


@dataclass
class AddressNftTransfer(Domain):
    address: str
    block_number: int
    log_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    token_address: str
    related_address: str
    transfer_type: int
    token_id: int
    value: int


@dataclass
class AddressTokenHolder(Domain):
    address: str
    token_address: str
    balance_of: str


@dataclass
class AddressTokenTransfer(Domain):
    address: str
    block_number: int
    log_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    token_address: str
    related_address: str
    transfer_type: int
    value: int


@dataclass
class AddressTransaction(Domain):
    address: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    txn_type: int
    related_address: str
    value: int
    transaction_fee: int
    receipt_status: int
    method: str


@dataclass
class TokenAddressNftInventory(Domain):
    token_address: str
    token_id: int
    wallet_address: str
