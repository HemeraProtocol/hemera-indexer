from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE
from sqlmodel import Field

from hemera.common.models import HemeraModel


class DailyTransactionsStats(HemeraModel, table=True):
    __tablename__ = "af_stats_na_daily_transactions"

    # Primary key field
    block_date: date = Field(sa_column=Column(DATE, primary_key=True))

    # Count fields
    cnt: Optional[int] = Field(default=None, sa_column=Column(BIGINT))
    total_cnt: Optional[int] = Field(default=None, sa_column=Column(BIGINT))
    txn_error_cnt: Optional[int] = Field(default=None, sa_column=Column(BIGINT))

    # Transaction fee statistics
    avg_transaction_fee: Optional[Decimal] = Field(default=None)
    avg_gas_price: Optional[Decimal] = Field(default=None)
    max_gas_price: Optional[Decimal] = Field(default=None)
    min_gas_price: Optional[Decimal] = Field(default=None)

    # L1 fee statistics
    avg_receipt_l1_fee: Optional[Decimal] = Field(default=None)
    max_receipt_l1_fee: Optional[Decimal] = Field(default=None)
    min_receipt_l1_fee: Optional[Decimal] = Field(default=None)

    # L1 gas price statistics
    avg_receipt_l1_gas_price: Optional[Decimal] = Field(default=None)
    max_receipt_l1_gas_price: Optional[Decimal] = Field(default=None)
    min_receipt_l1_gas_price: Optional[Decimal] = Field(default=None)

    __query_order__ = [block_date]
