from sqlalchemy import NUMERIC, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP

from common.models import HemeraModel, general_converter


class AaveV2ReserveRates(HemeraModel):
    __tablename__ = "af_aave_v2_reserve_rates"
    asset = Column(BYTEA, primary_key=True)

    liquidity_rate = Column(NUMERIC(100))
    stable_borrow_rate = Column(NUMERIC(100))
    variable_borrow_rate = Column(NUMERIC(100))
    liquidity_index = Column(NUMERIC(100))
    variable_borrow_index = Column(NUMERIC(100))

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
                "domain": "AaveV2ReserveDataCurrentD",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_aave_v2_reserve_rates.block_number",
                "converter": general_converter,
            },
        ]
