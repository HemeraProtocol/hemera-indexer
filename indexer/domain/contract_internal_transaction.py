from dataclasses import dataclass

from eth_utils import to_int

from indexer.domain import Domain


@dataclass
class ContractInternalTransaction(Domain):
    trace_id: str
    from_address: str
    to_address: str
    value: int
    trace_type: str
    call_type: str
    gas: int
    gas_used: int
    trace_address: str
    error: str
    status: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    trace_index: int
    input: str
    output: str

    @staticmethod
    def from_rpc(trace_dict: dict):
        return ContractInternalTransaction(
            trace_id=trace_dict["trace_id"],
            from_address=trace_dict["from_address"],
            to_address=trace_dict["to_address"],
            value=to_int(hexstr=trace_dict["value"]) if trace_dict["value"] else None,
            gas=to_int(hexstr=trace_dict["gas"]) if trace_dict["gas"] else None,
            gas_used=(to_int(hexstr=trace_dict["gas_used"]) if trace_dict["gas_used"] else None),
            trace_type=trace_dict["trace_type"],
            call_type=trace_dict["call_type"],
            trace_address=trace_dict["trace_address"],
            error=trace_dict["error"],
            status=trace_dict["status"],
            block_number=trace_dict["block_number"],
            block_hash=trace_dict["block_hash"],
            block_timestamp=trace_dict["block_timestamp"],
            transaction_index=trace_dict["transaction_index"],
            transaction_hash=trace_dict["transaction_hash"],
            trace_index=trace_dict["trace_index"],
            input=trace_dict["input"],
            output=trace_dict["output"],
        )

    def is_contract_creation(self):
        return self.trace_type == "create" or self.trace_type == "create2"
