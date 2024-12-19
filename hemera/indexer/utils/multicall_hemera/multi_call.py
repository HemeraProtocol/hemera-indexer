from typing import List, Optional

import orjson

from hemera.common.utils.format_utils import format_block_id, hex_str_to_bytes
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.abi import AGGREGATE_FUNC, TRY_BLOCK_AND_AGGREGATE_FUNC
from hemera.indexer.utils.multicall_hemera.constants import GAS_LIMIT, get_multicall_address, get_multicall_network
from hemera.indexer.utils.multicall_hemera.util import calculate_execution_time


class Multicall:

    def __init__(
        self,
        calls: List[Call],
        chain_id: int = None,
        block_number: Optional[int] = None,
        require_success: bool = True,
        gas_limit: int = GAS_LIMIT,
    ) -> None:
        self.calls = calls
        self.require_success = require_success
        self.gas_limit = gas_limit
        self.chain_id = chain_id
        self.block_number = block_number
        self.network = get_multicall_network(self.chain_id)
        if require_success is True:
            self.multicall_func = AGGREGATE_FUNC
        else:
            self.multicall_func = TRY_BLOCK_AND_AGGREGATE_FUNC
        self.multicall_address = get_multicall_address(self.network)
        self._parameters = None

    @calculate_execution_time
    def to_rpc_param(self):
        if self.require_success is True:
            parameters = [[[call.target, hex_str_to_bytes(call.data)] for call in self.calls]]
        else:
            parameters = [self.require_success, [[call.target, hex_str_to_bytes(call.data)] for call in self.calls]]

        call_data = self.multicall_func.encode_function_call_data(parameters)
        args = [{"to": self.multicall_address, "data": call_data}, format_block_id(self.block_number)]
        if self.gas_limit:
            args[0]["gas"] = format_block_id(self.gas_limit)
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": abs(hash(orjson.dumps(args))),
        }
