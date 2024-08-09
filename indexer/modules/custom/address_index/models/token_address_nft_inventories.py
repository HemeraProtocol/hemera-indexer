from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC

from common.models import HemeraModel, general_converter


class TokenAddressNftInventories(HemeraModel):
    __tablename__ = "token_address_nft_inventories"

    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA)
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TokenAddressNftInventory",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
