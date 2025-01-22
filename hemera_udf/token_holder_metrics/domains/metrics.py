from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class TokenHolderTransferWithPriceD(Domain):
    holder_address: str
    token_address: str
    block_number: int
    block_timestamp: int

    price_usd: float = 0.0
    transfer_amount: int = 0
    transfer_usd: float = 0.0
    transfer_action: str = "in"
    is_swap: bool = False
    tx_hash: str = ""
    log_index: int = 0


@dataclass
class TokenHolderMetricsD(Domain):
    holder_address: str
    token_address: str
    block_number: int
    block_timestamp: int

    first_block_timestamp: int
    last_swap_timestamp: int
    last_transfer_timestamp: int

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


@dataclass
class TokenHolderMetricsHistoryD(TokenHolderMetricsD):
    pass


@dataclass
class TokenHolderMetricsCurrentD(TokenHolderMetricsD):
    pass
