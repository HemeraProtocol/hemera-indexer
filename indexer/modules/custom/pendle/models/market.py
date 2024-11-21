from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.pendle.domains.market import PendlePoolD


class PendlePool(HemeraModel):
    __tablename__ = "af_pendle_pool"

    market_address = Column(BYTEA, primary_key=True)
    sy_address = Column(BYTEA)
    pt_address = Column(BYTEA)
    yt_address = Column(BYTEA)
    block_number = Column(BIGINT)
    chain_id = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": PendlePoolD,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
