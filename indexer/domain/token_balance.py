from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class TokenBalance(Domain):
    address: str
    token_id: int
    token_type: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class CurrentTokenBalance(Domain):
    address: str
    token_id: int
    token_type: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int

    @staticmethod
    def from_token_balance(token_balance: TokenBalance):
        return CurrentTokenBalance(
            address=token_balance.address,
            token_id=token_balance.token_id,
            token_type=token_balance.token_type,
            token_address=token_balance.token_address,
            balance=token_balance.balance,
            block_number=token_balance.block_number,
            block_timestamp=token_balance.block_timestamp,
        )
