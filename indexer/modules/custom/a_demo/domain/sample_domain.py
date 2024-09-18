from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from indexer.domain import FilterData


@dataclass
class ATransferD(FilterData):

    transaction_hash: str
    log_index: int
    transaction_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    transfer_from: Optional[str] = None
    transfer_to: Optional[str] = None
    value: Optional[int] = None


@dataclass
class SampleAddressCurrentD(FilterData):

    address: Optional[str] = None
    transaction_count: Optional[int] = None
    transfer_from_count: Optional[int] = None
    transfer_from_value: Optional[int] = None
    transfer_to_count: Optional[int] = None
    transfer_to_value: Optional[int] = None
    block_number = None


def sample_address_current_factory():
    return SampleAddressCurrentD(
        transaction_count=0,
        transfer_from_count=0,
        transfer_from_value=0,
        transfer_to_count=0,
        transfer_to_value=0,
    )
