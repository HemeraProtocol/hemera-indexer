import logging
from typing import Any, List, Optional, Tuple, Union

import orjson

from common.utils.format_utils import bytes_to_hex_str
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.abi import AGGREGATE_FUNC, TRY_BLOCK_AND_AGGREGATE_FUNC
from indexer.utils.multicall_hemera.constants import GAS_LIMIT, get_multicall_address, get_multicall_network

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


class Multicall(Call):

    def __init__(
        self,
        calls: List[Call],
        chain_id: int = None,
        block_number: Union[Optional[int], str] = None,
        require_success: bool = True,
        gas_limit: int = GAS_LIMIT,
    ) -> None:
        self.calls = calls
        self.block_number = block_number
        self.require_success = require_success
        self.gas_limit = gas_limit
        self.chain_id = chain_id
        self.network = get_multicall_network(self.chain_id)
        if require_success is True:
            self.multicall_func = AGGREGATE_FUNC
        else:
            self.multicall_func = TRY_BLOCK_AND_AGGREGATE_FUNC
        self.multicall_address = get_multicall_address(self.network)

        super().__init__(target=self.multicall_address, function_abi=self.multicall_func, gas_limit=self.gas_limit)

    def to_rpc_param(self):
        self.parameters = get_args(self.calls, self.require_success)
        args = self.prep_args()
        args[0]["data"] = bytes_to_hex_str(args[0]["data"])
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": abs(hash(orjson.dumps(args))),
        }
