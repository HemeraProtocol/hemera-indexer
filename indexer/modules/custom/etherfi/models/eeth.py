from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from indexer.modules.custom.etherfi.domains.eeth import (
    EtherFiPositionValuesD,
    EtherFiShareBalanceCurrentD,
    EtherFiShareBalanceD,
)


class EtherFiShareBalances(HemeraModel):
    __tablename__ = "ether_fi_share_balances"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    shares = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": EtherFiShareBalanceD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class CurrentEtherFiShareBalances(HemeraModel):
    __tablename__ = "ether_fi_share_balances_current"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    shares = Column(NUMERIC(100))
    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": EtherFiShareBalanceCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class EtherFiPositionValues(HemeraModel):
    __tablename__ = "ether_fi_position_values"

    block_number = Column(BIGINT, primary_key=True)
    total_share = Column(NUMERIC(100))
    total_value_out_lp = Column(NUMERIC(100))
    total_value_in_lp = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": EtherFiPositionValuesD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
