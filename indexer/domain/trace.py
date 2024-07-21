from dataclasses import dataclass, field
from typing import List

from common.models.traces import Traces
from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain


@dataclass
class Trace(Domain):
    trace_id: str
    from_address: str
    to_address: str
    value: int
    input: str
    output: str
    trace_type: str
    call_type: str
    gas: int
    gas_used: int
    subtraces: int
    error: str
    status: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    trace_index: int
    trace_address: List[int] = field(default_factory=list)

    def __init__(self, trace_dict: dict):
        self.dict_to_entity(trace_dict)

    def is_contract_creation(self):
        return self.trace_type == 'create' or self.trace_type == 'create2'

    def is_transfer_value(self):
        status = self.value is not None and self.value > 0

        return status and self.from_address != self.to_address and self.trace_type != 'delegatecall'


def format_trace_data(trace_dict):
    trace = {
        'model': Traces,
        'trace_id': trace_dict['trace_id'],
        'from_address': to_normalized_address(trace_dict['from_address']),
        'to_address': to_normalized_address(trace_dict['to_address']) if trace_dict['to_address'] else None,
        'value': to_int(hexstr=trace_dict['value']) if trace_dict['value'] else None,
        'input': trace_dict['input'],
        'output': trace_dict['output'],
        'trace_type': trace_dict['trace_type'],
        'call_type': trace_dict['call_type'],
        'gas': to_int(hexstr=trace_dict['gas']) if trace_dict['gas'] else None,
        'gas_used': to_int(hexstr=trace_dict['gas_used']) if trace_dict['gas_used'] else None,
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
