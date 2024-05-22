from exporters.jdbc.schema.traces import Traces
from utils.utils import hex_to_dec, to_normalized_address


def format_trace_data(trace_dict):
    trace = {
        'model': Traces,
        'trace_id': trace_dict['trace_id'],
        'from_address': to_normalized_address(trace_dict['from_address']),
        'to_address': to_normalized_address(trace_dict['to_address']),
        'value': hex_to_dec(trace_dict['value']),
        'input': trace_dict['input'],
        'output': trace_dict['output'],
        'trace_type': trace_dict['trace_type'],
        'call_type': trace_dict['call_type'],
        'gas': hex_to_dec(trace_dict['gas']),
        'gas_used': hex_to_dec(trace_dict['gas_used']),
        'subtraces': trace_dict['subtraces'],
        'trace_address': trace_dict['trace_address'],
        'error': trace_dict['error'],
        'status': trace_dict['status'],
        'block_number': trace_dict['block_number'],
        'block_hash': trace_dict['block_hash'],
        'block_timestamp': trace_dict['block_timestamp'],
        'transaction_index': trace_dict['transaction_index'],
        'transaction_hash': trace_dict['transaction_hash'],
        'trace_index': trace_dict['trace_index'],
    }

    return trace


def trace_is_contract_creation(trace):
    return trace['trace_type'] == 'create' or trace['trace_type'] == 'create2'


def trace_is_transfer_value(trace):
    return trace['value'] is not None and hex_to_dec(trace['value']) > 0 and \
        trace['from_address'] != trace['to_address'] and trace['trace_type'] != 'delegatecall'
