from datetime import datetime

from exporters.jdbc.schema.block_timestamp_mapper import BlockTimestampMapper


def format_block_ts_mapper(timestamp, block_number):
    block_ts_mapper = {
        "model": BlockTimestampMapper,
        'block_number': block_number,
        'timestamp': timestamp,
    }
    return block_ts_mapper
