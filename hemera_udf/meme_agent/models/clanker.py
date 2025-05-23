from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.meme_agent.domains.clanker import ClankerCreatedTokenD


class ClankerCreatedToken(HemeraModel):
    __tablename__ = "af_clanker_created_token"

    token_address = Column(BYTEA, primary_key=True)
    lp_nft_id = Column(BIGINT)
    deployer = Column(BYTEA)
    fid = Column(BIGINT)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    supply = Column(NUMERIC(100))
    locker_address = Column(BYTEA)
    cast_hash = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    version = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ClankerCreatedTokenD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
