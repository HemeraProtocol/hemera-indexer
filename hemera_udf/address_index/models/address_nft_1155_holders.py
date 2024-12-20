from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressNft1155Holder


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
                "domain": AddressNft1155Holder,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "address_nft_1155_holders_token_address_balance_of_idx",
    AddressNftTokenHolders.token_address,
    AddressNftTokenHolders.token_id,
    desc(AddressNftTokenHolders.balance_of),
)
