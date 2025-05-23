from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_transfer import ERC721TokenTransfer


class ERC721TokenTransfers(HemeraModel):
    __tablename__ = "erc721_token_transfers"

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    token_id = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index"),)
    __query_order__ = [block_number, log_index]

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


Index(
    "erc721_token_transfers_block_timestamp_index",
    desc(ERC721TokenTransfers.block_timestamp),
)
Index(
    "erc721_token_transfers_number_log_index",
    desc(ERC721TokenTransfers.block_number),
    desc(ERC721TokenTransfers.log_index),
)

Index(
    "erc721_token_transfers_from_address_number_log_index_index",
    ERC721TokenTransfers.from_address,
    desc(ERC721TokenTransfers.block_number),
    desc(ERC721TokenTransfers.log_index),
)
Index(
    "erc721_token_transfers_to_address_number_log_index_index",
    ERC721TokenTransfers.to_address,
    desc(ERC721TokenTransfers.block_number),
    desc(ERC721TokenTransfers.log_index),
)
Index(
    "erc721_token_transfers_token_address_number_log_index_index",
    ERC721TokenTransfers.token_address,
    desc(ERC721TokenTransfers.block_number),
    desc(ERC721TokenTransfers.log_index),
)
Index(
    "erc721_token_transfers_token_address_id_index",
    ERC721TokenTransfers.token_address,
    ERC721TokenTransfers.token_id,
)
Index(
    "erc721_token_transfers_token_address_from_index",
    ERC721TokenTransfers.token_address,
    ERC721TokenTransfers.from_address,
)
Index(
    "erc721_token_transfers_token_address_to_index",
    ERC721TokenTransfers.token_address,
    ERC721TokenTransfers.to_address,
)
