from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import TokenAddressNftInventory


class TokenAddressNftInventories(HemeraModel, table=True):
    __tablename__ = "token_address_nft_inventories"

    token_address: bytes = Field(primary_key=True)
    token_id: Decimal = Field(primary_key=True)
    wallet_address: bytes = Field()
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index(
            "token_address_nft_inventories_wallet_address_token_address__idx",
            "wallet_address",
            "token_address",
            "token_id",
        ),
    )

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
