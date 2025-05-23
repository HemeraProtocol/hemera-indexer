from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.merchant_moe.domains import MerchantMoePool


class FeatureMerchantMoePools(HemeraModel):
    __tablename__ = "af_merchant_moe_pools"
    position_token_address = Column(BYTEA, primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)
    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoePool,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
