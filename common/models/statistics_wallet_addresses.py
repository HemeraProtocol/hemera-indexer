from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, NUMERIC,BYTEA

from common.models import db


class StatisticsWalletAddresses(db.Model):
    address = Column(BYTEA, primary_key=True)
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
    txn_cnt = Column(INTEGER)
    internal_txn_cnt = Column(INTEGER)
    erc20_transfer_cnt = Column(INTEGER)
    erc721_transfer_cnt = Column(INTEGER)
    erc1155_transfer_cnt = Column(INTEGER)
    deposit_cnt = Column(INTEGER)
    withdraw_cnt = Column(INTEGER)
    tag = Column(VARCHAR)
