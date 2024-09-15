from datetime import datetime

from sqlalchemy import DATE, Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, SMALLINT, TEXT, TIMESTAMP

from common.models import HemeraModel, general_converter


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

    contract_creation_count = Column(INTEGER)
    contract_destruction_count = Column(INTEGER)
    contract_operation_count = Column(INTEGER)

    transaction_count = Column(
        INTEGER,
        generated=True,
        server_default=func.coalesce(transaction_in_count + transaction_out_count + transaction_self_count, 0),
    )
    internal_transaction_count = Column(
        INTEGER,
        generated=True,
        server_default=func.coalesce(
            internal_transaction_in_count + internal_transaction_out_count + internal_transaction_self_count, 0
        ),
    )
    erc20_transfer_count = Column(
        INTEGER,
        generated=True,
        server_default=func.coalesce(erc20_transfer_in_count + erc20_transfer_out_count + erc20_transfer_self_count, 0),
    )
    nft_transfer_count = Column(
        INTEGER,
        generated=True,
        server_default=func.coalesce(nft_transfer_in_count + nft_transfer_out_count + nft_transfer_self_count, 0),
    )
