from dataclasses import dataclass

from indexer.domains import Domain


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
