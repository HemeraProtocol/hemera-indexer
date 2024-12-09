from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from indexer.modules.custom.lido.domains.seth import LidoPositionValuesD, LidoShareBalanceCurrentD, LidoShareBalanceD


class LidoShareBalances(HemeraModel):
    __tablename__ = "af_lido_seth_share_balances"

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
                "domain": LidoShareBalanceD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class CurrentLidoShareBalances(HemeraModel):
    __tablename__ = "af_lido_seth_share_balances_current"

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
                "domain": LidoShareBalanceCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class LidoPositionValues(HemeraModel):
    __tablename__ = "af_lido_position_values"

    block_number = Column(BIGINT, primary_key=True)
    total_share = Column(NUMERIC(100))
    buffered_eth = Column(NUMERIC(100))
    consensus_layer = Column(NUMERIC(100))
    deposited_validators = Column(NUMERIC(100))
    cl_validators = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": LidoPositionValuesD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
