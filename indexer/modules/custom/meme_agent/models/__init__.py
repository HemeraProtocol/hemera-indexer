from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel
from indexer.modules.custom.hemera_ens.models.af_ens_node_current import ens_general_converter
from indexer.modules.custom.meme_agent.domains.clanker import ClankerCreatedTokenD


class ClankerCreatedToken(HemeraModel):
    __tablename__ = "clanker_created_token"

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

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ClankerCreatedTokenD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": ens_general_converter,
            }
        ]
