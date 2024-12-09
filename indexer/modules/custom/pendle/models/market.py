from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.pendle.domains.market import (
    PendlePoolD,
    PendleUserActiveBalanceCurrentD,
    PendleUserActiveBalanceD,
)


class PendlePool(HemeraModel):
    __tablename__ = "af_pendle_pool"

    market_address = Column(BYTEA, primary_key=True)
    sy_address = Column(BYTEA)
    pt_address = Column(BYTEA)
    yt_address = Column(BYTEA)
    underlying_asset = Column(BYTEA)
    block_number = Column(BIGINT)
    chain_id = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": PendlePoolD,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class PendleUserActiveBalance(HemeraModel):
    __tablename__ = "af_pendle_user_active_balance"

    market_address = Column(BYTEA, primary_key=True)
    user_address = Column(BYTEA, primary_key=True)
    sy_balance = Column(NUMERIC(100))
    active_balance = Column(NUMERIC(100))
    total_active_supply = Column(NUMERIC(100))
    market_sy_balance = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)
    chain_id = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": PendleUserActiveBalanceD,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class PendleUserActiveBalanceCurrent(HemeraModel):
    __tablename__ = "af_pendle_user_active_balance_current"

    market_address = Column(BYTEA, primary_key=True)
    user_address = Column(BYTEA, primary_key=True)
    sy_balance = Column(NUMERIC(100))
    active_balance = Column(NUMERIC(100))
    total_active_supply = Column(NUMERIC(100))
    market_sy_balance = Column(NUMERIC(100))
    block_number = Column(BIGINT)
    chain_id = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("market_address", "user_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": PendleUserActiveBalanceCurrentD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= af_pendle_user_active_balance_current.block_number",
                "converter": general_converter,
            }
        ]
