from datetime import datetime


def format_block_ts_mapper(timestamp, block_number):
    block_ts_mapper = {
        "model": "block_ts_mapper",
        'timestamp': timestamp,
        'block_number': block_number,
        'date_string': datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
    }
    return block_ts_mapper
