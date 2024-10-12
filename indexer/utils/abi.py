from typing import Any, Dict, Optional, Sequence, Tuple

from eth_abi.codec import ABICodec
from eth_abi.grammar import BasicType
from eth_typing import ChecksumAddress, HexStr, TypeStr
from eth_utils import (
    encode_hex,
    event_abi_to_log_topic,
    function_abi_to_4byte_selector,
    hexstr_if_str,
    is_binary_address,
    text_if_str,
    to_bytes,
    to_hex,
    to_text,
)
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.abi import build_strict_registry, get_abi_input_types, map_abi_data
from web3._utils.normalizers import implicitly_identity, parse_basic_type_str
from web3.types import ABIEvent, ABIFunction

from common.utils.format_utils import bytes_to_hex_str

codec = ABICodec(build_strict_registry())


def event_log_abi_to_topic(event_abi: ABIEvent) -> str:
    return bytes_to_hex_str(event_abi_to_log_topic(event_abi))


def function_abi_to_4byte_selector_str(function_abi: ABIFunction) -> str:
    # return 10 hex string
    return bytes_to_hex_str(function_abi_to_4byte_selector(function_abi))


def get_types_from_abi_type_list(abi_type_list: Sequence[Dict[str, Any]]) -> Sequence[str]:
    return [generate_type_str(abi_type) for abi_type in abi_type_list]


def generate_type_str(component):
    if component["type"] == "tuple[]":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")[]"
    elif component["type"] == "tuple":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")"
    else:
        return component["type"]


@implicitly_identity
def abi_string_to_text(type_str: TypeStr, data: Any) -> Optional[Tuple[TypeStr, str]]:
    if type_str == "string":
        return type_str, text_if_str(to_text, data)
    return None


@implicitly_identity
@parse_basic_type_str
def abi_bytes_to_bytes(abi_type: BasicType, type_str: TypeStr, data: Any) -> Optional[Tuple[TypeStr, HexStr]]:
    if abi_type.base == "bytes" and not abi_type.is_array:
        return type_str, hexstr_if_str(to_bytes, data)
    return None


@implicitly_identity
def abi_address_to_hex(type_str: TypeStr, data: Any) -> Optional[Tuple[TypeStr, ChecksumAddress]]:
    if type_str == "address":
        if is_binary_address(data):
            return type_str, Web3.to_checksum_address(data)
    return None


def encode_abi(
    abi: ABIFunction,
    arguments: Sequence[Any],
    data: str = None,
) -> HexStr:
    argument_types = get_abi_input_types(abi)

    normalizers = [
        abi_address_to_hex,
        abi_bytes_to_bytes,
        abi_string_to_text,
    ]

    normalized_arguments = map_abi_data(
        normalizers,
        argument_types,
        arguments,
    )
    encoded_arguments = codec.encode(
        argument_types,
        normalized_arguments,
    )
    if data:
        return to_hex(HexBytes(data) + encoded_arguments)
    else:
        return encode_hex(encoded_arguments)


def uint256_to_bytes(value: int) -> bytes:
    if value < 0 or value >= 2**256:
        raise ValueError("Value out of uint256 range")

    return value.to_bytes(32, byteorder="big")


def pad_address(address: str) -> bytes:
    address = address.lower().replace("0x", "")

    if len(address) != 40:
        raise ValueError("Invalid address length")

    padded = "0" * 24 + address
    return bytes.fromhex(padded)
