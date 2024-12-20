from sqlalchemy import Column, Index, desc
from sqlalchemy.dialects.postgresql import BIGINT, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.block_ts_mapper import BlockTsMapper


class BlockTimestampMapper(HemeraModel):
    __tablename__ = "block_ts_mapper"
    ts = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT)
    timestamp = Column(TIMESTAMP)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": BlockTsMapper,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("block_ts_mapper_idx", desc(BlockTimestampMapper.block_number))
