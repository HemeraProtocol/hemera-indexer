import logging
from typing import Any, List, Optional, Tuple, Union

import orjson

from common.utils.format_utils import bytes_to_hex_str
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.call import prep_args
from indexer.utils.multicall_hemera.constants import GAS_LIMIT, MULTICALL3_ADDRESSES, Network
from indexer.utils.multicall_hemera.signature import _get_signature

logger = logging.getLogger(__name__)
CallResponse = Tuple[Union[None, bool], bytes]


def get_args(calls: List[Call], require_success: bool = True) -> List[Union[bool, List[List[Any]]]]:
    if require_success is True:
        return [[[call.target, call.data] for call in calls]]
    return [require_success, [[call.target, call.data] for call in calls]]


def unpack_aggregate_outputs(outputs: Any) -> Tuple[CallResponse, ...]:
    return tuple((None, output) for output in outputs)


def unpack_batch_results(batch_results: List[List[CallResponse]]) -> List[CallResponse]:
    return [result for batch in batch_results for result in batch]


class Multicall:

    def __init__(
        self,
        calls: List[Call],
        chain_id: int = None,
        block_id: Union[Optional[int], str] = None,
        require_success: bool = True,
        gas_limit: int = GAS_LIMIT,
    ) -> None:
        self.calls = calls
        self.block_id = block_id
        self.require_success = require_success
        self.gas_limit = gas_limit
        self.chain_id = chain_id
        self.network = Network.from_value(self.chain_id)
        if require_success is True:
            multicall_map = MULTICALL3_ADDRESSES if self.network in MULTICALL3_ADDRESSES else None
            self.multicall_sig = "aggregate((address,bytes)[])(uint256,bytes[])"
        else:
            multicall_map = MULTICALL3_ADDRESSES if self.network in MULTICALL3_ADDRESSES else None
            self.multicall_sig = "tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])"
        self.multicall_address = multicall_map[self.network]

    @property
    def aggregate(self) -> Call:
        return Call(
            self.multicall_address,
            self.multicall_sig,
            returns=None,
            block_number=self.block_id,
            gas_limit=self.gas_limit,
        )

    def to_rpc_param(self):
        args = get_args(self.calls, self.require_success)
        args = prep_args(
            self.multicall_address, _get_signature(self.multicall_sig), args, self.block_id, hex(self.gas_limit)
        )
        args[0]["data"] = bytes_to_hex_str(args[0]["data"])
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": abs(hash(orjson.dumps(args))),
        }
