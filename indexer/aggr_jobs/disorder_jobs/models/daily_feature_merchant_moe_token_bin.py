from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, DATE
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class DailyFeatureMerChantMoeTokenBinRecords(HemeraModel):
    __tablename__ = "daily_feature_merchant_moe_token_bin_records"

    block_date = Column(DATE, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
