from datetime import datetime

from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class AddressTokenHolders(HemeraModel):
    __tablename__ = "address_token_holders"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    balance_of = Column(NUMERIC(100))
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressTokenHolder",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "address_token_holders_token_address_balance_of_idx",
    AddressTokenHolders.token_address,
    desc(AddressTokenHolders.balance_of),
)
