from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE, NUMERIC

from common.models import HemeraModel


class DailyTransactionsAggregates(HemeraModel):
    block_date = Column(DATE, primary_key=True)
    cnt = Column(BIGINT)
    total_cnt = Column(BIGINT)
    txn_error_cnt = Column(BIGINT)
    avg_transaction_fee = Column(NUMERIC)
    avg_gas_price = Column(NUMERIC)
    max_gas_price = Column(NUMERIC)
    min_gas_price = Column(NUMERIC)
    avg_receipt_l1_fee = Column(NUMERIC)
    max_receipt_l1_fee = Column(NUMERIC)
    min_receipt_l1_fee = Column(NUMERIC)
    avg_receipt_l1_gas_used = Column(NUMERIC)
    max_receipt_l1_gas_used = Column(NUMERIC)
    min_receipt_l1_gas_used = Column(NUMERIC)
    avg_receipt_l1_gas_price = Column(NUMERIC)
    max_receipt_l1_gas_price = Column(NUMERIC)
    min_receipt_l1_gas_price = Column(NUMERIC)
    avg_receipt_l1_fee_scalar = Column(NUMERIC)
    max_receipt_l1_fee_scalar = Column(NUMERIC)
    min_receipt_l1_fee_scalar = Column(NUMERIC)
