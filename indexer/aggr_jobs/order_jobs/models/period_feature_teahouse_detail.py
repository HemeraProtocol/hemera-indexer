from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, VARCHAR
from sqlalchemy.dialects.postgresql import BYTEA, DATE, INTEGER, NUMERIC, TIMESTAMP

from common.models import HemeraModel


class PeriodFeatureTeahouseDetail(HemeraModel):
    __tablename__ = "period_feature_teahouse_detail"

    # 主键字段
    period_date = Column(DATE, primary_key=True, nullable=False)
    position_token_address = Column(BYTEA, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True, nullable=False)
    share_percent = Column(NUMERIC, nullable=True)

    token_id = Column(INTEGER)

    # 其他字段
    pool_address = Column(BYTEA, nullable=False)
    liquidity = Column(NUMERIC, nullable=True)
    tick_upper = Column(INTEGER, nullable=True)
    tick_lower = Column(INTEGER, nullable=True)
    sqrt_price_x96 = Column(NUMERIC, nullable=True)
    token0_address = Column(BYTEA, nullable=True)
    token1_address = Column(BYTEA, nullable=True)
    token0_decimals = Column(INTEGER, nullable=True)
    token0_symbol = Column(VARCHAR, nullable=True)
    token1_decimals = Column(INTEGER, nullable=True)
    token1_symbol = Column(VARCHAR, nullable=True)

    # 创建时间字段
    create_time = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("period_date", "position_token_address", "wallet_address"),
    )

    # 索引：按日期分区或查询加速
    Index("period_feature_teahouse_detail_period_date_index", period_date)
