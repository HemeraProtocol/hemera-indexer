from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, Index, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera.common.models.token_transfers import BaseTokenTransfer
from hemera_udf.address_index.domains import AddressNftTransfer


class AddressNftTransfers(BaseTokenTransfer, HemeraModel, table=True):
    """Model for indexing NFT transfers by address"""

    __tablename__ = "address_nft_transfers"

    address: bytes = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    log_index: int = Field(primary_key=True)
    transaction_hash: bytes = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)
    token_id: Decimal = Field(primary_key=True)

    block_hash: bytes = Field(default=None)

    token_address: Optional[bytes] = Field(default=None)
    related_address: Optional[bytes] = Field(default=None)
    transfer_type: Optional[int] = Field(default=None)
    value: Optional[Decimal] = Field(default=None)

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_address_nft_transfers_token_time",
            text("address, block_timestamp DESC, block_number DESC, log_index DESC"),
        ),
    )

    __query_order__ = ["block_number", "log_index"]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressNftTransfer,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
