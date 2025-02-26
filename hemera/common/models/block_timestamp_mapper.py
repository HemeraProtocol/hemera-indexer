from datetime import datetime
from typing import Optional

from sqlalchemy import Index, text
from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.block_ts_mapper import BlockTsMapper


class BlockTimestampMapper(HemeraModel, table=True):
    __tablename__ = "block_ts_mapper"

    ts: int = Field(primary_key=True)
    block_number: Optional[int] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None)

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

    __table_args__ = Index("block_ts_mapper_idx", text("block_number DESC"))
