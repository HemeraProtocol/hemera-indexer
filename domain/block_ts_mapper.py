from datetime import datetime

from exporters.jdbc.schema.block_timestamp_mapper import BlockTimestampMapper


def format_block_ts_mapper(timestamp, block_number):
    block_ts_mapper = {
        "model": BlockTimestampMapper,
        'timestamp': timestamp,
        'block_number': block_number,
        'date_string': datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
    }
    return block_ts_mapper
