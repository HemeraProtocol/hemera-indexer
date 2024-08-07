import json
import logging
from itertools import groupby
from typing import List

from eth_utils import to_int

from common.utils.exception_control import HistoryUnavailableError
from enumeration.record_level import RecordLevel
from indexer.domain import dataclass_to_dict
from indexer.domain.block import Block, UpdateBlockInternalCount
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.domain.trace import Trace
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.json_rpc_requests import generate_trace_block_by_number_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()


# Exports traces
class ExportTracesJob(BaseJob):
    dependency_types = [Block]
    output_types = [Trace, ContractInternalTransaction, UpdateBlockInternalCount]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_web3_provider = kwargs["batch_web3_debug_provider"]
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["debug_batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["debug_batch_size"] > 1

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        self._batch_work_executor.execute(
            self._data_buff[Block.type()],
            self._collect_batch,
            total_items=len(self._data_buff[Block.type()]),
        )

        self._batch_work_executor.wait()

    def _collect_batch(self, blocks):
        traces = traces_rpc_requests(
            self._batch_web3_provider.make_request,
            [dataclass_to_dict(block) for block in blocks],
            self._is_batch,
        )

        for trace in traces:
            trace_entity = Trace.from_rpc(trace)
            self._collect_item(Trace.type(), trace_entity)
            if trace_entity.is_contract_creation() or trace_entity.is_transfer_value():
                self._collect_item(
                    ContractInternalTransaction.type(),
                    ContractInternalTransaction.from_rpc(trace),
                )

    def _process(self):
        self._data_buff[Trace.type()].sort(key=lambda x: (x.block_number, x.transaction_index, x.trace_index))

        self._data_buff[ContractInternalTransaction.type()].sort(
            key=lambda x: (x.block_number, x.transaction_index, x.trace_index)
        )

        for group_key, traces in groupby(self._data_buff[Trace.type()], lambda x: (x.block_number, x.block_hash)):
            block_number, block_hash = group_key
            traces_count = len(list(traces))
            internal_transactions_count = sum(1 for trace in traces if trace.is_contract_creation())
            self._data_buff[UpdateBlockInternalCount.type()].append(
                UpdateBlockInternalCount(
                    number=block_number,
                    hash=block_hash,
                    traces_count=traces_count,
                    internal_transactions_count=internal_transactions_count,
                )
            )


class ExtractTraces:

    def __init__(self):
        self._trace_idx = 0

    def geth_trace_to_traces(self, geth_trace):
        transaction_traces = geth_trace["transaction_traces"]

        traces = []

        for tx_index, tx in enumerate(transaction_traces):
            self._trace_idx = 0

            traces.extend(self._iterate_transaction_trace(geth_trace, tx_index, tx["txHash"], tx["result"]))

        return traces

    def _iterate_transaction_trace(self, geth_trace, tx_index, tx_hash, tx_trace, trace_address=[]):
        block_number = geth_trace["block_number"]
        transaction_index = tx_index
        trace_index = self._trace_idx

        self._trace_idx += 1
        trace_id = f"{block_number}_{transaction_index}_{trace_index}"

        # lowercase for compatibility with parity traces
        trace_type = tx_trace.get("type").lower()
        call_type = ""
        calls = tx_trace.get("calls", [])
        if trace_type == "selfdestruct":
            # rename to suicide for compatibility with parity traces
            trace_type = "suicide"

        elif trace_type in ("call", "callcode", "delegatecall", "staticcall"):
            call_type = trace_type
            trace_type = "call"

        trace = {
            "trace_id": trace_id,
            "from_address": tx_trace.get("from"),
            "to_address": tx_trace.get("to"),
            "input": tx_trace.get("input"),
            "output": tx_trace.get("output"),
            "value": tx_trace.get("value"),
            "gas": tx_trace.get("gas"),
            "gas_used": tx_trace.get("gasUsed"),
            "trace_type": trace_type,
            "call_type": call_type,
            "subtraces": len(calls),
            "trace_address": trace_address,
            "error": tx_trace.get("error"),
            "status": 1 if tx_trace.get("error") is None else 0,
            "block_number": block_number,
            "block_hash": geth_trace["block_hash"],
            "block_timestamp": geth_trace["block_timestamp"],
            "transaction_index": tx_index,
            "transaction_hash": tx_hash,
            "trace_index": self._trace_idx,
        }

        result = [trace]

        for call_index, call_trace in enumerate(calls):
            result.extend(
                self._iterate_transaction_trace(
                    geth_trace,
                    tx_index,
                    tx_hash,
                    call_trace,
                    trace_address + [call_index],
                )
            )

        return result


def traces_rpc_requests(make_requests, blocks: List[dict], is_batch):
    block_numbers = []
    for block in blocks:
        block["number"] = hex(block["number"])
        block_numbers.append(block["number"])
    trace_block_rpc = list(generate_trace_block_by_number_json_rpc(block_numbers))

    if is_batch:
        responses = make_requests(params=json.dumps(trace_block_rpc))
    else:
        responses = [make_requests(params=json.dumps(trace_block_rpc[0]))]

    total_traces = []
    for block, response in zip_rpc_response(blocks, responses, index="number"):
        block_number = block["number"]
        transactions = block["transactions"]
        try:
            result = rpc_response_to_result(response)
        except HistoryUnavailableError as e:
            exception_recorder.log(
                block_number=block_number,
                dataclass=Trace.type(),
                message_type=HistoryUnavailableError.__name__,
                message=e.message,
                level=RecordLevel.ERROR,
            )
            trace = {
                "trace_id": f"{to_int(hexstr=block_number)}_?_?",
                "block_number": to_int(hexstr=block_number),
                "block_hash": block["hash"],
                "block_timestamp": block["timestamp"],
                "transaction_index": 0,
                "trace_index": 0,
            }

            total_traces.append(trace)
            continue

        if "txHash" not in result[0]:
            if len(result) != len(transactions):
                raise ValueError("The number of traces is wrong " + str(result))

            for idx, trace_result in enumerate(result):
                trace_result["txHash"] = transactions[idx]["hash"]

        geth_trace = {
            "block_number": to_int(hexstr=block_number),
            "block_hash": block["hash"],
            "block_timestamp": block["timestamp"],
            "transaction_traces": result,
        }
        trace_spliter = ExtractTraces()
        traces = trace_spliter.geth_trace_to_traces(geth_trace)

        total_traces.extend(traces)

    return total_traces
