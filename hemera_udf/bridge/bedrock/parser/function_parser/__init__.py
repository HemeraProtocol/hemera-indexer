from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

from eth_typing import ABIFunction

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.utils.abi import function_abi_to_4byte_selector_str


class BedRockFunctionCallType(Enum):
    NATIVE_BRIDGE_ETH = 0

    BRIDGE_ETH = 1
    BRIDGE_ERC20 = 2
    BRIDGE_ERC721 = 3

    NORMAL_CROSS_CHAIN_CALL = 7


@dataclass
class BridgeRemoteFunctionCallInfo:
    bridge_from_address: str
    bridge_to_address: str
    local_token_address: Optional[str]
    remote_token_address: Optional[str]
    amount: int
    extra_info: dict
    remote_function_call_type: int


class RemoteFunctionCallDecoder:
    def __init__(
        self,
        function_abi: ABIFunction,
        decode_function: Callable[[bytes], BridgeRemoteFunctionCallInfo],
    ):
        self.function_abi = function_abi
        self.decode = decode_function
        self._4byte_selector = function_abi_to_4byte_selector_str(self.function_abi)

    def get_4byte_selector(self) -> str:
        return self._4byte_selector


class BedrockBridgeParser:
    def __init__(self, remote_function_call_decoders: List[RemoteFunctionCallDecoder]):
        self.remote_function_call_decoders = remote_function_call_decoders

    def get_remote_function_call_info(self, transaction_input: bytes) -> BridgeRemoteFunctionCallInfo:
        if len(transaction_input) < 4:
            raise ValueError("Input is too short to contain a function selector")
        selector = bytes_to_hex_str(transaction_input[:4]).lower()  # Assuming lowercase for consistency

        for decoder in self.remote_function_call_decoders:
            if decoder.get_4byte_selector() == selector:
                return decoder.decode(transaction_input)
        raise ValueError(f"Unknown function selector: {selector}")
