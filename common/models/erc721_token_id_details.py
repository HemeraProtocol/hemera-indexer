from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class ERC721TokenIdDetails(HemeraModel):
    __tablename__ = "erc721_token_id_details"

    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    token_owner = Column(BYTEA)
    token_uri = Column(VARCHAR)
    token_uri_info = Column(JSONB)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ERC721TokenIdDetail",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "UpdateERC721TokenIdDetail",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= erc721_token_id_details.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "erc721_detail_owner_address_id_index",
    desc(ERC721TokenIdDetails.token_owner),
    ERC721TokenIdDetails.token_address,
    ERC721TokenIdDetails.token_id,
)
