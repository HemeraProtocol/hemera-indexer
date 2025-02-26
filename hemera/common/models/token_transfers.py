from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import PrimaryKeyConstraint, text
from sqlmodel import Field, Index, SQLModel

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer


class BaseTokenTransfer(SQLModel):
    """Base model for all token transfers"""

    transaction_hash: bytes = Field(default=None)
    log_index: int = Field(default=None)
    from_address: Optional[bytes] = Field(default=None)
    to_address: Optional[bytes] = Field(default=None)
    token_address: Optional[bytes] = Field(default=None)

    block_number: Optional[int] = Field(default=None)
    block_hash: bytes = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)

    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reorg: Optional[bool] = Field(default=False)

    class Config:
        arbitrary_types_allowed = True


class ERC20TokenTransfers(BaseTokenTransfer, HemeraModel, table=True):
    """Model for ERC20 token transfers"""

    __tablename__ = "erc20_token_transfers"

    value: Optional[Decimal] = Field(default=None)

    __table_args__ = (
        PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index"),
        Index(
            "erc20_token_transfers_number_log_index", text("block_timestamp DESC, block_number DESC, log_index DESC")
        ),
        Index(
            "erc20_token_transfers_token_address_number_log_index_index",
            text("token_address,block_timestamp DESC, block_number DESC, log_index DESC"),
        ),
        Index(
            "erc20_token_transfers_token_address_from_index_index",
            text("token_address, from_address, block_timestamp DESC"),
        ),
        Index(
            "erc20_token_transfers_token_address_to_index_index",
            text("token_address, to_address, block_timestamp DESC"),
        ),
    )

    __query_order__ = ["block_number", "log_index"]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC20TokenTransfer,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class ERC721TokenTransfers(BaseTokenTransfer, table=True):
    """Model for ERC721 token transfers"""

    __tablename__ = "erc721_token_transfers"

    token_id: Optional[Decimal] = Field(default=None)

    __table_args__ = (
        PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index"),
        Index("erc721_token_transfers_block_timestamp_index", text("block_timestamp DESC")),
        Index("erc721_token_transfers_number_log_index", text("block_number DESC, log_index DESC")),
        Index(
            "erc721_token_transfers_token_address_number_log_index_index",
            text("token_address, block_number DESC, log_index DESC"),
        ),
        Index("erc721_token_transfers_token_address_id_index", text("token_address, token_id")),
        Index("erc721_token_transfers_token_address_from_index", text("token_address, from_address")),
        Index("erc721_token_transfers_token_address_to_index", text("token_address, to_address")),
    )

    __query_order__ = ["block_number", "log_index"]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC721TokenTransfer,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class ERC1155TokenTransfers(BaseTokenTransfer, table=True):
    """Model for ERC1155 token transfers"""

    __tablename__ = "erc1155_token_transfers"

    token_id: Decimal = Field(default=None)
    value: Optional[Decimal] = Field(default=None)

    __table_args__ = (
        PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index", "token_id"),
        Index(
            "erc1155_token_transfers_number_log_index", text("block_timestamp DESC, block_number DESC, log_index DESC")
        ),
        Index(
            "erc1155_token_transfers_token_address_number_log_index_index",
            text("token_address, block_timestamp DESC, block_number DESC, log_index DESC"),
        ),
        Index("erc1155_token_transfers_token_address_id_index", text("token_address, token_id, block_timestamp DESC")),
        Index(
            "erc1155_token_transfers_token_address_from_index",
            text("token_address, from_address, block_timestamp DESC"),
        ),
        Index(
            "erc1155_token_transfers_token_address_to_index", text("token_address, to_address, block_timestamp DESC")
        ),
    )

    __query_order__ = ["block_number", "log_index"]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC1155TokenTransfer,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class NftTransfers(HemeraModel, table=True):
    """
    Model for tracking nft(ERC721/ERC1155) transfer events.
    """

    __tablename__ = "nft_transfers"

    # Primary keys
    transaction_hash: bytes = Field(nullable=False, primary_key=True)
    block_hash: bytes = Field(nullable=False, primary_key=True)
    log_index: int = Field(nullable=False, primary_key=True)
    token_id: Decimal = Field(nullable=False, primary_key=True, max_digits=100)
    block_timestamp: datetime = Field(primary_key=True)
    block_number: int = Field(primary_key=True)

    # Transfer info
    from_address: Optional[bytes] = Field(default=None)
    to_address: Optional[bytes] = Field(default=None)
    token_address: Optional[bytes] = Field(default=None)
    value: Optional[Decimal] = Field(default=None, max_digits=100)

    # Metadata
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    reorg: bool = Field(default=False)

    # Query order specification
    __query_order__ = [block_timestamp, block_number, log_index]

    @staticmethod
    def model_domain_mapping():
        """
        Define the domain model mapping configuration.
        """
        return [
            {
                "domain": ERC1155TokenTransfer,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": ERC721TokenTransfer,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]

    __table_args__ = (
        # Block-based indices
        Index("idx_nft_transfers_block_log", text("block_timestamp DESC, block_number DESC, log_index DESC")),
        # Address-based indices with time
        Index(
            "idx_nft_transfers_token_time",
            text("token_address, block_timestamp DESC, block_number DESC, log_index DESC"),
        ),
        # Token-specific indices
        Index(
            "idx_nft_transfers_token_id",
            text("token_address, token_id, block_timestamp DESC, block_number DESC, log_index DESC"),
        ),
    )
