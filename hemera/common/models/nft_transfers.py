from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    PrimaryKeyConstraint,
    desc,
    func,
    text,
)

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_transfer import ERC721TokenTransfer, ERC1155TokenTransfer


class NftTransfers(HemeraModel):
    """
    Model for tracking nft(ERC721/ERC1155) transfer events.
    """

    __tablename__ = "nft_transfers"

    # Primary columns
    transaction_hash = Column(LargeBinary, nullable=False)
    block_hash = Column(LargeBinary, nullable=False)
    log_index = Column(Integer, nullable=False)
    token_id = Column(Numeric(100), nullable=False)

    # Transfer info
    from_address = Column(LargeBinary)
    to_address = Column(LargeBinary)
    token_address = Column(LargeBinary)
    value = Column(Numeric(100), nullable=True)

    # Block info
    block_number = Column(BigInteger)
    block_timestamp = Column(DateTime)

    # Metadata columns
    create_time = Column(DateTime, server_default=func.now(), nullable=False)
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    reorg = Column(Boolean, server_default=text("false"), nullable=False)

    # Table constraints
    __table_args__ = (
        PrimaryKeyConstraint(
            "transaction_hash",
            "block_timestamp",
            "block_number",
            "log_index",
            "block_hash",
            "token_id",
            name="pk_nft_transfers",
        ),
        # Block-based indices
        Index("idx_nft_transfers_block_log", desc(block_timestamp), desc(block_number), desc(log_index)),
        # Address-based indices with time
        Index(
            "idx_nft_transfers_token_time",
            token_address,
            desc(block_timestamp),
            desc(block_number),
            desc(log_index),
        ),
        # Token-specific indices
        Index(
            "idx_nft_transfers_token_id",
            token_address,
            token_id,
            desc(block_timestamp),
            desc(block_number),
            desc(log_index),
        ),
    )

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
