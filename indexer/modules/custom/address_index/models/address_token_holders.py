from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC

from common.models import HemeraModel, general_converter


class AddressTokenHolders(HemeraModel):
    __tablename__ = "address_token_holders"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    balance_of = Column(NUMERIC(100))
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "token_address"),)

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
