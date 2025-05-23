from sqlalchemy import NUMERIC, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.aave_v2.domains.aave_v2_domain import AaveV2ReserveD, AaveV2ReserveDataCurrentD


class AaveV2Reserve(HemeraModel):
    __tablename__ = "af_aave_v2_reserve"
    asset = Column(BYTEA, primary_key=True)
    asset_decimals = Column(NUMERIC(100))
    asset_symbol = Column(VARCHAR)

    a_token_address = Column(BYTEA)
    a_token_decimals = Column(NUMERIC(100))
    a_token_symbol = Column(VARCHAR)

    stable_debt_token_address = Column(BYTEA)
    stable_debt_token_decimals = Column(NUMERIC(100))
    stable_debt_token_symbol = Column(VARCHAR)

    variable_debt_token_address = Column(BYTEA)
    variable_debt_token_decimals = Column(NUMERIC(100))
    variable_debt_token_symbol = Column(VARCHAR)

    interest_rate_strategy_address = Column(BYTEA)

    liquidity_rate = Column(NUMERIC(100))
    stable_borrow_rate = Column(NUMERIC(100))
    variable_borrow_rate = Column(NUMERIC(100))
    liquidity_index = Column(NUMERIC(100))
    variable_borrow_index = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
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
                "domain": AaveV2ReserveD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= af_aave_v2_reserve.block_number",
                "converter": general_converter,
            },
            {
                "domain": AaveV2ReserveDataCurrentD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= af_aave_v2_reserve.block_number",
                "converter": general_converter,
            },
        ]
