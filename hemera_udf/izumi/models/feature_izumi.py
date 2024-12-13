from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.izumi.domains.feature_uniswap_v3 import (
    IzumiPool,
    IzumiPoolCurrentPrice,
    IzumiPoolPrice,
    IzumiSwapEvent,
    IzumiTokenCurrentState,
    IzumiTokenState,
)


class IzumiPools(HemeraModel):
    __tablename__ = "af_izumi_pools"
    position_token_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)

    factory_address = Column(BYTEA)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)
    fee = Column(NUMERIC(100))

    point_delta = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    # For Izumi
    pool_id = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiPool,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class IzumiPoolCurrentPrices(HemeraModel):
    __tablename__ = "af_izumi_pool_prices_current"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    factory_address = Column(BYTEA)

    sqrt_price_x96 = Column(NUMERIC(100))
    current_point = Column(BIGINT)
    liquidity = Column(NUMERIC(100))
    liquidity_x = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiPoolCurrentPrice,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_izumi_pool_prices_current.block_number",
                "converter": general_converter,
            },
        ]


class IzumiPoolPrices(HemeraModel):
    __tablename__ = "af_izumi_pool_prices_hist"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    sqrt_price_x96 = Column(NUMERIC(100))
    current_point = Column(BIGINT)
    liquidity = Column(NUMERIC(100))
    liquidity_x = Column(NUMERIC(100))

    factory_address = Column(BYTEA)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiPoolPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class IzumiTokenCurrentStates(HemeraModel):
    __tablename__ = "af_izumi_token_state_current"

    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    wallet_address = Column(BYTEA)

    pool_address = Column(BYTEA)
    pool_id = Column(INTEGER)

    left_pt = Column(BIGINT)
    right_pt = Column(BIGINT)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiTokenCurrentState,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_izumi_token_state_current.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "af_izumi_token_state_current_wallet_desc_index",
    desc(IzumiTokenCurrentStates.wallet_address),
)


class IzumiTokenStates(HemeraModel):
    __tablename__ = "af_izumi_token_state_hist"

    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    wallet_address = Column(BYTEA)

    pool_address = Column(BYTEA)
    pool_id = Column(INTEGER)

    left_pt = Column(BIGINT)
    right_pt = Column(BIGINT)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiTokenState,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "af_izumi_token_state_hist_token_block_desc_index",
    desc(IzumiTokenStates.position_token_address),
    desc(IzumiTokenStates.block_timestamp),
)

Index(
    "af_izumi_token_state_hist_wallet_token_block_desc_index",
    desc(IzumiTokenStates.wallet_address),
    desc(IzumiTokenStates.position_token_address),
    desc(IzumiTokenStates.block_timestamp),
)


# We don't really need this, token state table should work
# class IzumiTokens(HemeraModel):
#     __tablename__ = "af_izumi_tokens"

#     position_token_address = Column(BYTEA, primary_key=True)
#     token_id = Column(NUMERIC(100), primary_key=True)

#     pool_address = Column(BYTEA)
#     tick_lower = Column(NUMERIC(100))
#     tick_upper = Column(NUMERIC(100))
#     fee = Column(NUMERIC(100))

#     block_number = Column(BIGINT)
#     block_timestamp = Column(BIGINT)

#     create_time = Column(TIMESTAMP, server_default=func.now())
#     update_time = Column(TIMESTAMP, server_default=func.now())

#     __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

#     @staticmethod
#     def model_domain_mapping():
#         return [
#             {
#                 "domain": IzumiToken,
#                 "conflict_do_update": True,
#                 "update_strategy": None,
#                 "converter": general_converter,
#             },
#         ]


class IzumiSwapRecords(HemeraModel):
    __tablename__ = "af_izumi_swap_hist"
    pool_address = Column(BYTEA, primary_key=True)
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    position_token_address = Column(BYTEA)
    transaction_from_address = Column(BYTEA)
    sender = Column(BYTEA)
    recipient = Column(BYTEA)

    current_point = Column(BIGINT)
    fee = Column(BIGINT)
    sell_x_earn_y = Column(BOOLEAN)
    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("pool_address", "transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": IzumiSwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
