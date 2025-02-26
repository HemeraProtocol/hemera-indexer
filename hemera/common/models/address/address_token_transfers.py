from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressTokenTransfer


class AddressTokenTransfers(HemeraModel, table=True):
    """Model for indexing token transfers by address"""

    __tablename__ = "address_token_transfers"

    # Primary keys
    address: bytes = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    log_index: int = Field(primary_key=True)
    transaction_hash: bytes = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)
    block_hash: bytes = Field(primary_key=True)

    # Transfer data
    token_address: Optional[bytes] = Field(default=None)
    related_address: Optional[bytes] = Field(default=None)
    transfer_type: Optional[int] = Field(default=None)
    value: Optional[Decimal] = Field(default=None)

    # Metadata
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressTokenTransfer,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
