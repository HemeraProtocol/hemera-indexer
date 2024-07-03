import json
import logging

from domain.contract_internal_transaction import trace_to_contract_internal_transaction
from domain.trace import format_trace_data, trace_is_contract_creation, trace_is_transfer_value
from enumeration.entity_type import EntityType
from executors.batch_work_executor import BatchWorkExecutor
from exporters.console_item_exporter import ConsoleItemExporter
from utils.enrich import enrich_traces
from utils.json_rpc_requests import generate_trace_block_by_number_json_rpc
from jobs.base_job import BaseJob
from utils.utils import validate_range, rpc_response_to_result

logger = logging.getLogger(__name__)


# Exports traces
class ExportTracesJob(BaseJob):
    def __init__(self,
                 index_keys,
                 entity_types,
                 start_block,
                 end_block,
                 batch_web3_provider,
                 batch_size,
                 max_workers,
                 item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        validate_range(start_block, end_block)
        self._start_block = start_block
        self._end_block = end_block
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(
            range(self._start_block, self._end_block + 1),
            self._collect_batch,
            total_items=self._end_block - self._start_block + 1
        )

        self._batch_work_executor.shutdown()

    def _collect_batch(self, block_number_batch):
        traces = traces_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)

        for trace in traces:
            trace['item'] = 'trace'
            self._collect_item(trace)

    def _process(self):

        self._data_buff['enriched_traces'] = [format_trace_data(trace)
                                              for trace in enrich_traces(self._data_buff['formated_block'],
                                                                         self._data_buff['trace'])]

        self._data_buff['enriched_traces'] = sorted(self._data_buff['enriched_traces'],
                                                    key=lambda x: (
                                                        x['block_number'], x['transaction_index'], x['trace_index']))

        self._data_buff['internal_transaction'] = [trace_to_contract_internal_transaction(trace)
                                                   for trace in self._data_buff['enriched_traces']
                                                   if trace_is_contract_creation(trace) or
                                                   trace_is_transfer_value(trace, True)]

    def _export(self):
        if self._entity_types & EntityType.TRACE:
            items = self._extract_from_buff(['enriched_traces', 'internal_transaction'])
            self._item_exporter.export_items(items)


class ExtractTraces:

    def __init__(self):
        self._trace_idx = 0

    def geth_trace_to_traces(self, geth_trace):
        block_number = geth_trace['block_number']
        transaction_traces = geth_trace['transaction_traces']

        traces = []

        for tx_index, tx in enumerate(transaction_traces):
            self._trace_idx = 0

            traces.extend(self._iterate_transaction_trace(
                block_number,
                tx_index,
                tx['txHash'],
                tx['result']
            ))

        return traces

    def _iterate_transaction_trace(self, block_number, tx_index, tx_hash, tx_trace, trace_address=[]):
        block_number = block_number
        transaction_index = tx_index
        trace_index = self._trace_idx

        self._trace_idx += 1
        trace_id = f"{block_number}_{transaction_index}_{trace_index}"

        from_address = tx_trace.get('from')
        to_address = tx_trace.get('to')

        input = tx_trace.get('input')
        output = tx_trace.get('output')

        value = tx_trace.get('value')
        gas = tx_trace.get('gas')
        gas_used = tx_trace.get('gasUsed')

        error = tx_trace.get('error')
        status = 1 if error is None else 0

        # lowercase for compatibility with parity traces
        trace_type = tx_trace.get('type').lower()
        call_type = ''
        calls = tx_trace.get('calls', [])
        if trace_type == 'selfdestruct':
            # rename to suicide for compatibility with parity traces
            trace_type = 'suicide'

        elif trace_type in ('call', 'callcode', 'delegatecall', 'staticcall'):
            call_type = trace_type
            trace_type = 'call'

        trace = {
            'trace_id': trace_id,
            'from_address': from_address,
            'to_address': to_address,
            'input': input,
            'output': output,
            'value': value,
            'gas': gas,
            'gas_used': gas_used,
            'trace_type': trace_type,
            'call_type': call_type,
            'subtraces': len(calls),
            'trace_address': trace_address,
            'error': error,
            'status': status,
            'block_number': block_number,
            'transaction_index': tx_index,
            'transaction_hash': tx_hash,
            'trace_index': self._trace_idx,
        }

        result = [trace]

        for call_index, call_trace in enumerate(calls):
            result.extend(self._iterate_transaction_trace(
                block_number,
                tx_index,
                tx_hash,
                call_trace,
                trace_address + [call_index],
            ))

        return result


def traces_rpc_requests(make_requests, block_batch, is_batch):
    trace_block_rpc = list(generate_trace_block_by_number_json_rpc(block_batch))

    if is_batch:
        response = make_requests(params=json.dumps(trace_block_rpc))
    else:
        response = [make_requests(params=json.dumps(trace_block_rpc[0]))]

    total_traces = []
    for response_item in response:
        block_number = response_item.get('id')
        result = rpc_response_to_result(response_item)

        geth_trace = {
            'block_number': block_number,
            'transaction_traces': result,
        }
        trace_spliter = ExtractTraces()
        traces = trace_spliter.geth_trace_to_traces(geth_trace)

        total_traces.extend(traces)

    return total_traces
