from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class ERC20TokenTransferWithPriceD(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    value: int
    price: float
    decimals: int
    is_swap: bool
    from_address_balance: int  # balance after transfer
    to_address_balance: int  # balance after transfer
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class TokenHolderMetricsD(Domain):
    holder_address: str
    token_address: str
    block_number: int
    block_timestamp: int

    first_block_timestamp: int
    last_swap_timestamp: int
    last_transfer_timestamp: int
    last_price: float = 0.0
    current_balance: int = 0
    max_balance: int = 0
    max_balance_timestamp: int = 0
    sell_25_timestamp: int = 0
    sell_50_timestamp: int = 0

    total_buy_count: int = 0
    total_buy_amount: int = 0
    total_buy_usd: float = 0.0

    total_sell_count: int = 0
    total_sell_amount: int = 0
    total_sell_usd: float = 0.0

    swap_buy_count: int = 0
    swap_buy_amount: int = 0
    swap_buy_usd: float = 0.0

    swap_sell_count: int = 0
    swap_sell_amount: int = 0
    swap_sell_usd: float = 0.0

    success_sell_count: int = 0
    fail_sell_count: int = 0

    current_average_buy_price: float = 0.0

    realized_pnl: float = 0.0
    sell_pnl: float = 0.0
    win_rate: float = 0.0
    pnl_valid: bool = False


@dataclass
class TokenHolderMetricsHistoryD(TokenHolderMetricsD):
    pass


@dataclass
class TokenHolderMetricsCurrentD(TokenHolderMetricsD):
    pass
