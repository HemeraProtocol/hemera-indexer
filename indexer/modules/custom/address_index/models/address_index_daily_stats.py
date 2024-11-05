from sqlalchemy import DATE, Column
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class AddressIndexDailyStats(HemeraModel):
    __tablename__ = "af_index_daily_stats"

    address = Column(BYTEA, primary_key=True)
    block_date = Column(DATE, primary_key=True)

    transaction_in_count = Column(INTEGER)
    transaction_out_count = Column(INTEGER)
    transaction_self_count = Column(INTEGER)

    transaction_in_value = Column(BIGINT)
    transaction_out_value = Column(BIGINT)
    transaction_self_value = Column(BIGINT)

    transaction_in_fee = Column(NUMERIC)
    transaction_out_fee = Column(NUMERIC)
    transaction_self_fee = Column(NUMERIC)

    internal_transaction_in_count = Column(INTEGER)
    internal_transaction_out_count = Column(INTEGER)
    internal_transaction_self_count = Column(INTEGER)

    internal_transaction_in_value = Column(BIGINT)
    internal_transaction_out_value = Column(BIGINT)
    internal_transaction_self_value = Column(BIGINT)

    erc20_transfer_in_count = Column(INTEGER)
    erc20_transfer_out_count = Column(INTEGER)
    erc20_transfer_self_count = Column(INTEGER)

    nft_transfer_in_count = Column(INTEGER)
    nft_transfer_out_count = Column(INTEGER)
    nft_transfer_self_count = Column(INTEGER)

    nft_721_transfer_in_count = Column(INTEGER)
    nft_721_transfer_out_count = Column(INTEGER)
    nft_721_transfer_self_count = Column(INTEGER)

    nft_1155_transfer_in_count = Column(INTEGER)
    nft_1155_transfer_out_count = Column(INTEGER)
    nft_1155_transfer_self_count = Column(INTEGER)

    contract_creation_count = Column(INTEGER)
    contract_destruction_count = Column(INTEGER)
    contract_operation_count = Column(INTEGER)

    transaction_count = Column(
        INTEGER,
    )
    internal_transaction_count = Column(
        INTEGER,
    )
    erc20_transfer_count = Column(
        INTEGER,
    )

    nft_transfer_count = Column(INTEGER)
    nft_721_transfer_count = Column(INTEGER)
    nft_1155_transfer_count = Column(INTEGER)
