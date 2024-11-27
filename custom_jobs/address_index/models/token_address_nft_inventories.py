from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from custom_jobs.address_index.domain import TokenAddressNftInventory


class TokenAddressNftInventories(HemeraModel):
    __tablename__ = "token_address_nft_inventories"

    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenAddressNftInventory,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "token_address_nft_inventories_wallet_address_token_address__idx",
    TokenAddressNftInventories.wallet_address,
    TokenAddressNftInventories.token_address,
    TokenAddressNftInventories.token_id,
)
