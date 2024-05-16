from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP

from exporters.jdbc.schema import Base


class BlockTimestampMapper(Base):
    __tablename__ = 'block_ts_mapper'
    ts = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT)
    timestamp = Column(TIMESTAMP)
