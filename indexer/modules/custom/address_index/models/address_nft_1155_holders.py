from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC

from common.models import HemeraModel, general_converter


class AddressNftTokenHolders(HemeraModel):
    __tablename__ = "address_nft_1155_holders"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    balance_of = Column(NUMERIC(100))
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressNft1155Holder",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
