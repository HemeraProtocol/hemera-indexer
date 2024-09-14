from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, NUMERIC, TIMESTAMP

from common.models import HemeraModel


class PeriodFeatureMerChantMoeTokenBinRecords(HemeraModel):
    __tablename__ = "af_merchant_moe_token_bin_hist_period"

    period_date = Column(DATE, primary_key=True)
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("period_date", "position_token_address", "token_id"),)
