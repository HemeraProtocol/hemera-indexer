import logging
from typing import Any, List, Optional, Sequence, Union

import orjson
from eth_typing import Address, ChecksumAddress, HexAddress
from eth_typing.abi import Decodable
from eth_utils import to_checksum_address

from common.utils.abi_code_utils import Function
from common.utils.format_utils import bytes_to_hex_str, format_block_id, hex_str_to_bytes

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
        self.target = to_checksum_address(target)
        self.block_number = block_number
        self.gas_limit = gas_limit

        self.function_abi = function_abi
        self.parameters = parameters
        self.user_defined_k = user_defined_k
        self.returns = None
        self.call_id = None

    def __repr__(self) -> str:
        return f"<Call {self.function_abi.get_name()} on {self.target[:8]}>"

    @property
    def data(self) -> bytes:
        return hex_str_to_bytes(self.function_abi.encode_function_call_data(self.parameters or []))

    def decode_output(self, output: Decodable) -> Any:
        try:
            decoded = self.function_abi.decode_function_output_data(bytes_to_hex_str(output))
            return decoded
        except Exception as e:
            logger.error(f"Failed to decode output of {self.function_abi.get_name()} data {bytes_to_hex_str(output)}")
            raise e
            return None

    def to_rpc_param(self):
        args = self.prep_args()
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": abs(hash(orjson.dumps(args))),
        }

    def prep_args(self) -> List:
        call_data = self.function_abi.encode_function_call_data(self.parameters if self.parameters else [])
        args = [{"to": self.target, "data": call_data}, format_block_id(self.block_number)]
        if self.gas_limit:
            args[0]["gas"] = self.gas_limit
        return args
