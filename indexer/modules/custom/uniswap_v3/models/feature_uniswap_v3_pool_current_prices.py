from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3PoolCurrentPrices(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_prices_current"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    factory_address = Column(BYTEA)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3PoolCurrentPrice",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_uniswap_v3_pool_prices_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": "AgniV3PoolCurrentPrice",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_uniswap_v3_pool_prices_current.block_number",
                "converter": general_converter,
            },
        ]
