from sqlalchemy import BOOLEAN, INTEGER, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.token_holder_metrics.domains.metrics import (
    ERC20TokenTransferWithPriceD,
    TokenHolderMetricsCurrentD,
    TokenHolderMetricsHistoryD,
)


class TokenHolderMetricsCurrent(HemeraModel):
    __tablename__ = "af_token_holder_metrics_current"

    holder_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    current_balance = Column(NUMERIC)
    max_balance = Column(NUMERIC)
    max_balance_timestamp = Column(TIMESTAMP)
    sell_25_timestamp = Column(TIMESTAMP)
    sell_50_timestamp = Column(TIMESTAMP)

    total_buy_count = Column(BIGINT)
    total_buy_amount = Column(NUMERIC)
    total_buy_usd = Column(NUMERIC)

    total_sell_count = Column(BIGINT)
    total_sell_amount = Column(NUMERIC)
    total_sell_usd = Column(NUMERIC)

    swap_buy_count = Column(BIGINT)
    swap_buy_amount = Column(NUMERIC)
    swap_buy_usd = Column(NUMERIC)

    swap_sell_count = Column(BIGINT)
    swap_sell_amount = Column(NUMERIC)
    swap_sell_usd = Column(NUMERIC)

    last_transfer_timestamp = Column(TIMESTAMP)
    last_swap_timestamp = Column(TIMESTAMP)
    last_price = Column(NUMERIC)
    success_sell_count = Column(BIGINT)
    fail_sell_count = Column(BIGINT)

    current_average_buy_price = Column(NUMERIC)

    realized_pnl = Column(NUMERIC)
    sell_pnl = Column(NUMERIC)
    win_rate = Column(NUMERIC)
    pnl_valid = Column(BOOLEAN)

    first_block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("holder_address", "token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenHolderMetricsCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class TokenHolderMetricsHistory(HemeraModel):
    __tablename__ = "af_token_holder_metrics_history"

    holder_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    current_balance = Column(NUMERIC)
    max_balance = Column(NUMERIC)
    max_balance_timestamp = Column(TIMESTAMP)
    sell_25_timestamp = Column(TIMESTAMP)
    sell_50_timestamp = Column(TIMESTAMP)

    total_buy_count = Column(BIGINT)
    total_buy_amount = Column(NUMERIC)
    total_buy_usd = Column(NUMERIC)

    total_sell_count = Column(BIGINT)
    total_sell_amount = Column(NUMERIC)
    total_sell_usd = Column(NUMERIC)

    swap_buy_count = Column(BIGINT)
    swap_buy_amount = Column(NUMERIC)
    swap_buy_usd = Column(NUMERIC)

    swap_sell_count = Column(BIGINT)
    swap_sell_amount = Column(NUMERIC)
    swap_sell_usd = Column(NUMERIC)

    last_transfer_timestamp = Column(TIMESTAMP)
    last_swap_timestamp = Column(TIMESTAMP)
    last_price = Column(NUMERIC)

    success_sell_count = Column(BIGINT)
    fail_sell_count = Column(BIGINT)

    current_average_buy_price = Column(NUMERIC)

    realized_pnl = Column(NUMERIC)
    sell_pnl = Column(NUMERIC)
    win_rate = Column(NUMERIC)
    pnl_valid = Column(BOOLEAN)

    first_block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("holder_address", "token_address", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenHolderMetricsHistoryD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class ERC20TokenTransfersWithPrice(HemeraModel):
    __tablename__ = "af_erc20_token_transfers_with_price"

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    price = Column(NUMERIC)
    decimals = Column(NUMERIC(100))
    is_swap = Column(BOOLEAN)
    from_address_balance = Column(NUMERIC(100))
    to_address_balance = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index", "block_timestamp"),)
    __query_order__ = [block_number, log_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC20TokenTransferWithPriceD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
