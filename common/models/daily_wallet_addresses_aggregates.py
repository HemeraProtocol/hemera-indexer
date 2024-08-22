from sqlalchemy import DATE, Column, Computed, Index
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyWalletAddressesAggregates(HemeraModel):
    __tablename__ = "daily_wallet_addresses_aggregates"

    address = Column(BYTEA, primary_key=True, nullable=False)
    block_date = Column(DATE, primary_key=True, nullable=False)
    txn_in_cnt = Column(INTEGER, default=0)
    txn_out_cnt = Column(INTEGER, default=0)
    txn_in_value = Column(NUMERIC(78))
    txn_out_value = Column(NUMERIC(78))
    internal_txn_in_cnt = Column(INTEGER, default=0)
    internal_txn_out_cnt = Column(INTEGER, default=0)
    internal_txn_in_value = Column(NUMERIC(78))
    internal_txn_out_value = Column(NUMERIC(78))
    erc20_transfer_in_cnt = Column(INTEGER, default=0)
    erc721_transfer_in_cnt = Column(INTEGER, default=0)
    erc1155_transfer_in_cnt = Column(INTEGER, default=0)
    erc20_transfer_out_cnt = Column(INTEGER, default=0)
    erc721_transfer_out_cnt = Column(INTEGER, default=0)
    erc1155_transfer_out_cnt = Column(INTEGER, default=0)

    internal_txn_cnt = Column(INTEGER, Computed("internal_txn_in_cnt + internal_txn_out_cnt"))
    erc20_transfer_cnt = Column(INTEGER, Computed("erc20_transfer_in_cnt + erc20_transfer_out_cnt"))
    erc721_transfer_cnt = Column(INTEGER, Computed("erc721_transfer_in_cnt + erc721_transfer_out_cnt"))
    erc1155_transfer_cnt = Column(INTEGER, Computed("erc1155_transfer_in_cnt + erc1155_transfer_out_cnt"))

    txn_self_cnt = Column(INTEGER, default=0)
    txn_in_error_cnt = Column(INTEGER, default=0)
    txn_out_error_cnt = Column(INTEGER, default=0)
    txn_self_error_cnt = Column(INTEGER, default=0)

    txn_cnt = Column(INTEGER, Computed("((txn_in_cnt + txn_out_cnt) - txn_self_cnt)"))

    deposit_cnt = Column(INTEGER, default=0)
    withdraw_cnt = Column(INTEGER, default=0)
    gas_in_used = Column(NUMERIC(78), default=0)
    l2_txn_in_fee = Column(NUMERIC(78), default=0)
    l1_txn_in_fee = Column(NUMERIC(78), default=0)
    txn_in_fee = Column(NUMERIC(78), default=0)
    gas_out_used = Column(NUMERIC(78), default=0)
    l2_txn_out_fee = Column(NUMERIC(78), default=0)
    l1_txn_out_fee = Column(NUMERIC(78), default=0)
    txn_out_fee = Column(NUMERIC(78), default=0)
    contract_deployed_cnt = Column(INTEGER, default=0)
    from_address_unique_interacted_cnt = Column(INTEGER, default=0)
    to_address_unique_interacted_cnt = Column(INTEGER, default=0)

# could be replaced by partition in case of huge amount data
Index("daily_wallet_addresses_aggregates_block_date_index", DailyWalletAddressesAggregates.block_date)
