from sqlalchemy import Column, Index, desc
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP

from common.models import HemeraModel


class BlockTimestampMapper(HemeraModel):
    __tablename__ = 'block_ts_mapper'
    ts = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT)
    timestamp = Column(TIMESTAMP)


Index('block_ts_mapper_idx', desc(BlockTimestampMapper.block_number))
