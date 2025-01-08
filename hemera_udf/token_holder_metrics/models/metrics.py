from sqlalchemy import Column, PrimaryKeyConstraint, func, BOOLEAN
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.token_holder_metrics.domains.metrics import TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD


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

    success_sell_count = Column(BIGINT)
    fail_sell_count = Column(BIGINT)

    current_average_buy_price = Column(NUMERIC)

    realized_pnl = Column(NUMERIC)
    win_rate = Column(NUMERIC)

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
    
    holder_address = Column(BYTEA)
    token_address = Column(BYTEA)
    block_number = Column(BIGINT)
    tx_hash = Column(BYTEA)
    log_index = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    price_usd = Column(NUMERIC)
    transfer_amount = Column(NUMERIC)
    transfer_usd = Column(NUMERIC)
    transfer_action = Column(VARCHAR)
    is_swap = Column(BOOLEAN)

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("holder_address", "token_address", "block_number", "tx_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenHolderMetricsHistoryD,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
