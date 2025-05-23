from dataclasses import dataclass

from hemera.indexer.domains import Domain


# records for all token
@dataclass
class AfStakedTransferredBalanceHistDomain(Domain):
    contract_address: str
    protocol_id: str
    wallet_address: str
    token_address: str
    block_transfer_value: int
    block_cumulative_value: int
    block_number: int
    block_timestamp: int


@dataclass
class AfStakedTransferredBalanceCurrentDomain(Domain):
    contract_address: str
    protocol_id: str
    wallet_address: str
    token_address: str
    block_transfer_value: int
    block_cumulative_value: int
    block_number: int
    block_timestamp: int


@dataclass
class StakedFBTCDetail(Domain):
    vault_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class StakedFBTCCurrentStatus(Domain):
    vault_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class TransferredFBTCDetail(Domain):
    vault_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class TransferredFBTCCurrentStatus(Domain):
    vault_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int
