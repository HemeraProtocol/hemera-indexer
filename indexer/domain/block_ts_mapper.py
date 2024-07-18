from dataclasses import dataclass

from common.models.block_timestamp_mapper import BlockTimestampMapper
from indexer.domain import Domain


@dataclass
class BlockTsMapper(Domain):
    block_number: int
    timestamp: int


def format_block_ts_mapper(timestamp, block_number):
    block_ts_mapper = {
        "model": BlockTimestampMapper,
        'block_number': block_number,
        'timestamp': timestamp,
    }
    return block_ts_mapper
