from exporters.jdbc.schema.logs import Logs
from eth_utils import to_int, to_normalized_address


def format_log_data(log_dict):
    log = {
        'model': Logs,
        'log_index': to_int(hexstr=log_dict['logIndex']),
        'address': to_normalized_address(log_dict['address']),
        'data': log_dict['data'],
        'topic0': log_dict['topics'][0],
        'topic1': log_dict['topics'][1] if len(log_dict['topics']) > 1 else None,
        'topic2': log_dict['topics'][2] if len(log_dict['topics']) > 2 else None,
        'topic3': log_dict['topics'][3] if len(log_dict['topics']) > 3 else None,
        'transaction_hash': log_dict['transactionHash'],
        'transaction_index': to_int(hexstr=log_dict['transactionIndex']),
        'block_number': to_int(hexstr=log_dict['blockNumber']),
        'block_hash': log_dict['blockHash'],
        'block_timestamp': log_dict['blockTimestamp']
    }
    return log
