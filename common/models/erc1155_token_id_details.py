from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class ERC1155TokenIdDetails(HemeraModel):
    __tablename__ = "erc1155_token_id_details"

    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    token_supply = Column(NUMERIC(78))
    token_uri = Column(VARCHAR)
    token_uri_info = Column(JSONB)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ERC1155TokenIdDetail",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "UpdateERC1155TokenIdDetail",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= erc1155_token_id_details.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "erc1155_detail_desc_address_id_index",
    desc(ERC1155TokenIdDetails.token_address),
    ERC1155TokenIdDetails.token_id,
)
