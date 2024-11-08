from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV2Pools(HemeraModel):
    __tablename__ = "feature_uniswap_v2_pools"
    factory_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    length = Column(NUMERIC(100))

    called_block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("factory_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2Pool",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
