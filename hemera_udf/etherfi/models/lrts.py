from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.etherfi.domains import EtherFiLrtExchangeRateD


class EtherFiLrtExchangeRate(HemeraModel):
    __tablename__ = "af_ether_fi_lrt_exchange_rate"

    token_address = Column(BYTEA, primary_key=True)
    exchange_rate = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("token_address", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": EtherFiLrtExchangeRateD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
