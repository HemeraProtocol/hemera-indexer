from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor


class ExtractGethTracesJob(BaseJob):
    def __init__(
            self,
            traces_iterable,
            batch_size,
            max_workers,
            index_keys):
        self.traces_iterable = traces_iterable
        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

        self.trace_idx = 0

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.traces_iterable, self._extract_geth_traces)

    def _extract_geth_traces(self, geth_traces):
        for geth_trace in geth_traces:
            traces = self.geth_trace_to_traces(geth_trace)
            for trace in traces:
                trace['item'] = 'trace'
                self._export_item(trace)

    def geth_trace_to_traces(self, geth_trace):
        block_number = geth_trace['block_number']
        transaction_traces = geth_trace['transaction_traces']

        traces = []

        for tx_index, tx_trace in enumerate(transaction_traces):
            self.trace_idx = 0

            traces.extend(self._iterate_transaction_trace(
                block_number,
                tx_index,
                tx_trace,
            ))

        return traces

    def _iterate_transaction_trace(self, block_number, tx_index, tx_trace, trace_address=[]):

        block_number = block_number
        transaction_index = tx_index
        trace_index = self.trace_idx

        self.trace_idx += 1
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
            'trace_index': self.trace_idx,
        }

        result = [trace]

        for call_index, call_trace in enumerate(calls):
            result.extend(self._iterate_transaction_trace(
                block_number,
                tx_index,
                call_trace,
                trace_address + [call_index],
            ))

        return result

    def _end(self):
        self.batch_work_executor.shutdown()
