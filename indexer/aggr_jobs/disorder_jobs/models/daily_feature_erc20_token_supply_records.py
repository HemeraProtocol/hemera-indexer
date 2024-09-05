from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, DATE
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class DailyFeatureErc20TokenSupplyRecords(HemeraModel):
    __tablename__ = "daily_feature_erc20_token_supply_records"

    block_date = Column(DATE, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())