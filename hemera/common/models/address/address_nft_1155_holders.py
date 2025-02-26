from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, desc, func
from sqlmodel import Field, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressNft1155Holder


class AddressNftTokenHolders(HemeraModel, table=True):
    __tablename__ = "address_nft_1155_holders"

    address: bytes = Field(primary_key=True)
    token_address: bytes = Field(primary_key=True)
    token_id: Decimal = Field(primary_key=True)
    balance_of: Optional[Decimal] = Field(default=None)

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressNft1155Holder,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_nft_1155_holders_token_address_balance_of_idx",
            "token_address",
            "token_id",
            desc("balance_of"),
        ),
    )
