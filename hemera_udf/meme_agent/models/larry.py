from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.meme_agent.domains.larry import LarryCreatedTokenD


class LarryCreatedToken(HemeraModel):
    __tablename__ = "af_larry_created_token"

    token = Column(BYTEA, primary_key=True)
    party = Column(BYTEA)
    recipient = Column(BYTEA)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    eth_value = Column(NUMERIC(100))
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": LarryCreatedTokenD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
