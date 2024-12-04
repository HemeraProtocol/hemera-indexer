from datetime import datetime

from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, func, BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, JSONB, NUMERIC

from common.models import HemeraModel


class PeriodFeatureDefiWalletCmethDetail(HemeraModel):
    __tablename__ = "period_feature_defi_wallet_cmeth_detail"

    period_date = Column(DATE, primary_key=True)
    wallet_address = Column(String, primary_key=True)
    chain_name = Column(String, primary_key=True)
    contracts = Column(JSONB)

    total_cmeth_balance = Column(NUMERIC)
    total_cmeth_usd = Column(NUMERIC)
    wallet_holding_cmeth_balance = Column(NUMERIC)
    wallet_holding_cmeth_usd = Column(NUMERIC)
    updated_version = Column(INTEGER)
    total_protocol_cmeth_balance = Column(NUMERIC)
    total_protocol_cmeth_usd = Column(NUMERIC)
    rank = Column(INTEGER)
    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("period_feature_defi_wallet_cmeth_detail_period_date", PeriodFeatureDefiWalletCmethDetail.period_date)