from dataclasses import dataclass

from hemera.indexer.domains import Domain
from hemera.indexer.domains.transaction import Transaction


@dataclass
class Contract(Domain):
    address: str
    name: str
    contract_creator: str
    creation_code: str
    deployed_code: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    transaction_from_address: str

    def __init__(self, contract: dict):
        self.dict_to_entity(contract)

    def fill_transaction_from_address(self, address: str):
        self.transaction_from_address = address


def extract_contract_from_trace(trace):
    contract = {
        "address": trace.to_address,
        "contract_creator": trace.from_address,
        "creation_code": trace.input,
        "deployed_code": trace.output,
        "block_number": trace.block_number,
        "block_hash": trace.block_hash,
        "block_timestamp": trace.block_timestamp,
        "transaction_index": trace.transaction_index,
        "transaction_hash": trace.transaction_hash,
    }

    return contract


@dataclass
class ContractFromTransaction(Domain):
    address: str
    name: str
    contract_creator: str
    creation_code: str
    deployed_code: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    transaction_from_address: str

    def __init__(self, contract: dict):
        self.dict_to_entity(contract)

    def fill_transaction_from_address(self, address: str):
        self.transaction_from_address = address


def extract_contract_from_transaction(transaction: Transaction):
    contract = {
        "address": transaction.receipt.contract_address,
        "contract_creator": transaction.from_address,
        "creation_code": transaction.input,
        "block_number": transaction.block_number,
        "block_hash": transaction.block_hash,
        "block_timestamp": transaction.block_timestamp,
        "transaction_index": transaction.transaction_index,
        "transaction_hash": transaction.hash,
        "transaction_from_address": transaction.from_address,
    }

    return contract
