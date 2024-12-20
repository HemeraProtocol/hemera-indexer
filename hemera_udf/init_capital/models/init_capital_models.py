from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, JSONB, NUMERIC, SMALLINT, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.init_capital import (
    InitCapitalPoolHistoryDomain,
    InitCapitalPoolUpdateDomain,
    InitCapitalPositionCreateDomain,
    InitCapitalPositionHistoryDomain,
    InitCapitalPositionUpdateDomain,
    InitCapitalRecordDomain,
)


class InitCapitalPositionHistory(HemeraModel):
    __tablename__ = "init_capital_position_history"

    position_id = Column(NUMERIC(100), primary_key=True)
    owner_address = Column(BYTEA)
    viewer_address = Column(BYTEA)
    mode = Column(INTEGER)

    collaterals = Column(JSONB)
    borrows = Column(JSONB)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": InitCapitalPositionHistoryDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class InitCapitalPositionCurrent(HemeraModel):
    __tablename__ = "init_capital_position_current"

    position_id = Column(NUMERIC(100), primary_key=True)
    owner_address = Column(BYTEA)
    viewer_address = Column(BYTEA)
    mode = Column(INTEGER)

    collaterals = Column(JSONB)
    borrows = Column(JSONB)

    created_block_number = Column(BIGINT)
    created_block_timestamp = Column(TIMESTAMP)
    created_transaction_hash = Column(BYTEA)
    created_log_index = Column(INTEGER)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": InitCapitalPositionCreateDomain,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= init_capital_position_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": InitCapitalPositionUpdateDomain,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= init_capital_position_current.block_number",
                "converter": general_converter,
            },
        ]


class InitCapitalRecords(HemeraModel):
    __tablename__ = "init_capital_record"

    # 1 -> collaterize  2 -> borrow 3 -> decollaterize 4 -> repay 5 -> liquidate
    action_type = Column(SMALLINT)
    position_id = Column(NUMERIC(100))
    pool_address = Column(BYTEA)
    token_address = Column(BYTEA)
    amount = Column(NUMERIC(100))
    share = Column(NUMERIC(100))
    address = Column(BYTEA)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": InitCapitalRecordDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


"""
    uint private constant VIRTUAL_SHARES = 10 ** 8;
    uint private constant VIRTUAL_ASSETS = 1;

    function toAmt(uint _shares) public view returns (uint amt) {
        return _amt.mulDiv(totalAssets() + VIRTUAL_ASSETS, totalSupply() + VIRTUAL_SHARES);
    }
    function debtShareToAmtStored(uint _shares) public view returns (uint amt) {
        amt = totalDebtShares > 0 ? _shares.mulDiv(totalDebt, totalDebtShares, MathUpgradeable.Rounding.Up) : 0;
    }
"""


class InitCapitalPoolsHistory(HemeraModel):
    __tablename__ = "init_capital_pool_history"

    pool_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA)
    total_asset = Column(NUMERIC(100))
    total_supply = Column(NUMERIC(100))
    total_debt = Column(NUMERIC(100))
    total_debt_share = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": InitCapitalPoolHistoryDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class InitCapitalPoolCurrent(HemeraModel):
    __tablename__ = "init_capital_pool_current"

    pool_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA)
    total_asset = Column(NUMERIC(100))
    total_supply = Column(NUMERIC(100))
    total_debt = Column(NUMERIC(100))
    total_debt_share = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": InitCapitalPoolUpdateDomain,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= init_capital_pool_current.block_number OR init_capital_pool_current.block_number IS NULL",
                "converter": general_converter,
            }
        ]


# class InitCapitalAddressCurrent(HemeraModel):
#     __tablename__ = "init_capital_address"

#     address = Column(BYTEA, primary_key=True)


# class InitCapitalAddressCurrent(HemeraModel):
#     __tablename__ = "init_capital_address_current"

#     address = Column(BYTEA, primary_key=True)
