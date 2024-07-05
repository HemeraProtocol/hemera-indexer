from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP, VARCHAR

from exporters.jdbc.schema import Base


class RPCStatistic(Base):
    __tablename__ = 'rpc_statistic'

    rpc_endpoint = Column(VARCHAR, primary_key=True)
    call_method = Column(VARCHAR, primary_key=True)
    caller_name = Column(VARCHAR, primary_key=True)
    statistic_count = Column(BIGINT)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('rpc_endpoint', 'call_method', 'caller_name'),
    )
