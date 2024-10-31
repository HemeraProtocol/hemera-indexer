from sqlalchemy import NUMERIC, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP

from common.models import HemeraModel, general_converter


class AaveV1Reserve(HemeraModel):
    __tablename__ = "af_aave_v1_reserve"
    asset = Column(BYTEA, primary_key=True)
    asset_decimals = Column(NUMERIC(100))
    asset_symbol = Column(VARCHAR)

    a_token_address = Column(BYTEA)
    a_token_decimals = Column(NUMERIC(100))
    a_token_symbol = Column(VARCHAR)

    interest_rate_strategy_address = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("asset"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AaveV1ReserveD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
