from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP, VARCHAR

from common.models import HemeraModel
from indexer.modules.custom.meme_agent.domains.virtuals import VirtualsCreatedTokenD
from indexer.modules.custom.hemera_ens.models.af_ens_node_current import ens_general_converter

class VirtualsCreatedToken(HemeraModel):
    __tablename__ = "af_virtuals_created_token"

    virtual_id = Column(BIGINT, primary_key=True)
    token = Column(BYTEA)
    dao = Column(BYTEA)
    tba = Column(BYTEA)
    ve_token = Column(BYTEA)
    lp = Column(BYTEA)
    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": VirtualsCreatedTokenD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": ens_general_converter,
            }
        ]
