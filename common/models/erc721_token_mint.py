from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class ERC721TokenMint(HemeraModel):
    __tablename__ = "erc721_token_mint"

    ip_account = Column(BYTEA, primary_key=True)
    nft_contract = Column(BYTEA, primary_key=True)
    nft_id = Column(NUMERIC(100), primary_key=True)
    chain_id = Column(BIGINT)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("ip_account", "nft_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ERC721TokenMint",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "erc721_token_mint_address_id_index",
    ERC721TokenMint.ip_account,
    ERC721TokenMint.nft_id,
)