from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, Computed, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, JSONB, TIMESTAMP, VARCHAR
from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.contract import Contract, ContractFromTransaction


class Contracts(HemeraModel, table=True):
    __tablename__ = "contracts"

    # Primary key
    address: bytes = Field(primary_key=True)

    # Basic contract information
    name: Optional[str] = Field(default=None)
    contract_creator: Optional[bytes] = Field(default=None)
    creation_code: Optional[bytes] = Field(default=None)
    deployed_code: Optional[bytes] = Field(default=None)

    # Block and transaction details
    block_number: Optional[int] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)
    transaction_index: Optional[int] = Field(default=None)
    transaction_hash: Optional[bytes] = Field(default=None)
    transaction_from_address: Optional[bytes] = Field(default=None)

    # Additional contract metadata
    official_website: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    social_list: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    is_verified: bool = Field(default=False)
    is_proxy: Optional[bool] = Field(default=None)
    implementation_contract: Optional[bytes] = Field(default=None)
    verified_implementation_contract: Optional[bytes] = Field(default=None)
    proxy_standard: Optional[str] = Field(default=None)

    # Metadata fields
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reorg: bool = Field(default=False, sa_column=Column(BOOLEAN, server_default=text("false")))
    deployed_code_hash: Optional[str] = Field(
        default=None,
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Contract,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": ContractFromTransaction,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
