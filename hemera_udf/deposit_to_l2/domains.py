from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class AddressTokenDeposit(Domain):
    wallet_address: str
    chain_id: int
    contract_address: str
    token_address: str
    value: int
    block_number: int
    block_timestamp: int


@dataclass
class TokenDepositTransaction(Domain):
    transaction_hash: str
    wallet_address: str
    chain_id: int
    contract_address: str
    token_address: str
    value: int
    block_number: int
    block_timestamp: int
