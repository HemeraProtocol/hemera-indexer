import logging
from typing import Any, List, Optional, Sequence, Union

import orjson
from eth_typing import Address, ChecksumAddress, HexAddress
from eth_utils import to_checksum_address

from hemera.common.utils.abi_code_utils import Function
from hemera.common.utils.format_utils import format_block_id

logger = logging.getLogger(__name__)

AnyAddress = Union[str, Address, ChecksumAddress, HexAddress]


class Call:

    def __init__(
        self,
        target: AnyAddress,
        function_abi: Function,
        parameters: Sequence[Any] = None,
        block_number: Optional[int] = None,
        gas_limit: Optional[int] = None,
        user_defined_k: Optional[Any] = None,
    ) -> None:
        # self.target = to_checksum_address(target)
        self.target = target
        self.block_number = block_number
        self.gas_limit = gas_limit

        self.function_abi = function_abi
        self.parameters = parameters
        self.user_defined_k = user_defined_k
        self.returns = None
        self.call_id = None
        self._data = None
        self._rpc_params = None

    def __repr__(self) -> str:
        return f"<Call {self.function_abi.get_name()} on {self.target[:8]}>"

    @property
    def data(self) -> str:
        if self._data is None:
            self._data = self.function_abi.encode_function_call_data(self.parameters or [])
        return self._data

    def decode_output(self, hex_str) -> Any:
        try:
            if hex_str and hex_str != "0x":
                decoded = self.function_abi.decode_function_output_data(hex_str)
                return decoded
        except Exception as e:
            logger.debug(f"Failed to decode output of {self.function_abi.get_name()} data {hex_str}")
            # raise e
            return None

    @property
    def rpc_param(self):
        if self._rpc_params is None:
            args = self.prep_args()
            self._rpc_params = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": args,
                "id": abs(hash(orjson.dumps(args))),
            }
        return self._rpc_params

    def prep_args(self) -> List:
        call_data = self.data
        args = [{"to": self.target, "data": call_data}, format_block_id(self.block_number)]
        if self.gas_limit:
            args[0]["gas"] = format_block_id(self.gas_limit)
        return args
