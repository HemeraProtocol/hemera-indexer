import logging
from typing import Any, List, Optional, Union

import orjson

from common.utils.format_utils import format_block_id
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.abi import AGGREGATE_FUNC, TRY_BLOCK_AND_AGGREGATE_FUNC
from indexer.utils.multicall_hemera.constants import GAS_LIMIT, get_multicall_address, get_multicall_network

logger = logging.getLogger(__name__)


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
        self.parameters = self.get_args(self.require_success)

    def get_args(self, require_success: bool = True) -> List[Union[bool, List[List[Any]]]]:
        if require_success is True:
            return [[[call.target, call.data] for call in self.calls]]
        return [require_success, [[call.target, call.data] for call in self.calls]]

    def to_rpc_param(self):
        args = self.prep_args()
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": abs(hash(orjson.dumps(args))),
        }

    def prep_args(self) -> List:
        call_data = self.multicall_func.encode_function_call_data(self.parameters if self.parameters else [])
        args = [{"to": self.multicall_address, "data": call_data}, format_block_id(self.block_number)]
        if self.gas_limit:
            args[0]["gas"] = self.gas_limit
        return args
