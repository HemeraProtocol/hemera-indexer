from common.models import HemeraModel, general_converter
from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera_udf.thena.domains.feature_thena import ThenaSharesDomain


class AfThenaShares(HemeraModel):
    __tablename__ = "af_thena_shares"

    pool_address = Column(BYTEA, primary_key=True)
    farming_address = Column(BYTEA, primary_key=True)
    gamma_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)

    shares = Column(NUMERIC)
    total_supply = Column(NUMERIC)
    tick_lower = Column(NUMERIC)
    tick_upper = Column(NUMERIC)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("farming_address", "pool_address", "gamma_address", "wallet_address", "block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ThenaSharesDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
