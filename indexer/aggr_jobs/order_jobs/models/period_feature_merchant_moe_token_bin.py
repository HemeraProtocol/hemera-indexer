from datetime import datetime

from sqlalchemy import DATE, Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class PeriodFeatureMerChantMoeTokenBinRecords(HemeraModel):
    __tablename__ = "af_merchant_moe_token_bin_hist_period"

    period_date = Column(DATE, primary_key=True)
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())