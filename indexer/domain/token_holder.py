from dataclasses import dataclass

from indexer.domain import Domain
from indexer.domain.token_balance import TokenBalance


@dataclass
class ERC20TokenHolder(Domain):
    token_address: str
    wallet_address: str
    balance_of: int
    block_number: int
    block_timestamp: int

    def __init__(self, token_balance: TokenBalance):
        self.token_address = token_balance.token_address
        self.wallet_address = token_balance.address
        self.balance_of = token_balance.balance
        self.block_number = token_balance.block_number
        self.block_timestamp = token_balance.block_timestamp


@dataclass
class ERC721TokenHolder(Domain):
    token_address: str
    wallet_address: str
    balance_of: int
    block_number: int
    block_timestamp: int

    def __init__(self, token_balance: TokenBalance):
        self.token_address = token_balance.token_address
        self.wallet_address = token_balance.address
        self.balance_of = token_balance.balance
        self.block_number = token_balance.block_number
        self.block_timestamp = token_balance.block_timestamp


@dataclass
class ERC1155TokenHolder(Domain):
    token_address: str
    wallet_address: str
    token_id: int
    balance_of: int
    latest_call_contract_time: int
    block_number: int
    block_timestamp: int

    def __init__(self, token_balance: TokenBalance):
        self.token_address = token_balance.token_address
        self.wallet_address = token_balance.address
        self.token_id = token_balance.token_id
        self.balance_of = token_balance.balance
        self.latest_call_contract_time = token_balance.block_timestamp
        self.block_number = token_balance.block_number
        self.block_timestamp = token_balance.block_timestamp
