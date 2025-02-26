from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, desc
from sqlmodel import Field, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressTokenHolder


class AddressTokenHolders(HemeraModel, table=True):
    __tablename__ = "address_token_holders"

    address: bytes = Field(primary_key=True)
    token_address: bytes = Field(primary_key=True)
    balance_of: Decimal = Field()
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressTokenHolder,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_token_holders_token_address_balance_of_idx",
            "token_address",
            desc("balance_of"),
        ),
    )
