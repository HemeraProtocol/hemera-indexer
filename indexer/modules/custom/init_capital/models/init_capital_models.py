from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import SMALLINT, INTEGER, BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class InitCapitalPositionHistory(HemeraModel):
    __tablename__ = "init_capital_position_history"

    position_id = Column(NUMERIC(100), primary_key=True)
    owner_address = Column(BYTEA)
    viewer_address = Column(BYTEA)
    mode = Column(INTEGER)

    collateral_pool_address = Column(BYTEA)
    collateral_token_addres = Column(BYTEA)
    collateral_amount = Column(NUMERIC(100))

    borrow_pool_address = Column(BYTEA)
    borrow_token_address = Column(BYTEA)
    borrow_share = Column(NUMERIC(100))
    borrow_amount = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "InitCapitalPositionHistoryDomain",
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

    collateral_pool_address = Column(BYTEA)
    collateral_token_addres = Column(BYTEA)
    collateral_amount = Column(NUMERIC(100))

    borrow_pool_address = Column(BYTEA)
    borrow_token_address = Column(BYTEA)
    borrow_share = Column(NUMERIC(100))
    borrow_amount = Column(NUMERIC(100))

    created_block_number = Column(BIGINT)
    created_block_timestamp = Column(TIMESTAMP)
    created_transaction_hash = Column(BYTEA)
    created_log_index = Column(INTEGER)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "InitCapitalPositionCreateDomain",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "InitCapitalPositionUpdateDomain",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

class InitCapitalRecords(HemeraModel):
    __tablename__ = "init_capital_record"

    # 1 -> collaterize  2 -> borrow 3 -> decollaterize 4 -> repay
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

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "InitCapitalRecord",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


# class InitCapitalAddressCurrent(HemeraModel):
#     __tablename__ = "init_capital_address"

#     address = Column(BYTEA, primary_key=True)



# class InitCapitalAddressCurrent(HemeraModel):
#     __tablename__ = "init_capital_address_current"

#     address = Column(BYTEA, primary_key=True)