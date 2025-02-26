from itertools import accumulate
from typing import Any, Dict, Optional, Sequence, Tuple

from eth_abi.codec import ABICodec
from eth_abi.grammar import BasicType
from eth_typing import ABIEvent, ABIFunction, ChecksumAddress, HexStr, TypeStr
from eth_utils import (
    event_abi_to_log_topic,
    function_abi_to_4byte_selector,
    hexstr_if_str,
    is_binary_address,
    text_if_str,
    to_bytes,
    to_text,
)
from web3 import Web3
from web3._utils.abi import build_strict_registry
from web3._utils.normalizers import implicitly_identity, parse_basic_type_str

from hemera.common.utils.format_utils import bytes_to_hex_str

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


def uint256_to_bytes(value: int) -> bytes:
    return value.to_bytes(32, byteorder="big")


def pad_address(address: str) -> bytes:
    address = address.lower().replace("0x", "")

    if len(address) != 40:
        raise ValueError("Invalid address length")

    padded = "0" * 24 + address
    return bytes.fromhex(padded)


def encode_bool(arg: bool) -> bytes:
    value = b"\x01" if arg is True else b"\x00"
    return zpad(value, 32)


def encode_bytes(value: bytes) -> bytes:
    value_length = len(value)

    encoded_size = uint256_to_bytes(value_length)
    padded_value = zpad_right(value, ceil32(value_length))

    return encoded_size + padded_value


def tuple_encode(values, type_lis):
    raw_head_chunks = []
    tail_chunks = []
    for value, tp in zip(values, type_lis):
        if tp == "bytes":
            raw_head_chunks.append(None)
            tail_chunks.append(encode_bytes(value))
        elif tp == "bool":
            raw_head_chunks.append(encode_bool(value))
            tail_chunks.append(b"")
        elif tp == "address":
            raw_head_chunks.append(pad_address(value))
            tail_chunks.append(b"")
        elif tp == "(address,bytes)[]":
            items_are_dynamic = True
            if not items_are_dynamic or len(value) == 0:
                return b"".join(tail_chunks)
            encoded_size = uint256_to_bytes(len(value))

            tmp_tail_chunks = tuple(tuple_encode(list(i), ["address", "bytes"]) for i in value)
            head_length = 32 * len(value)
            tail_offsets = (0,) + tuple(accumulate(map(len, tmp_tail_chunks[:-1])))
            head_chunks = tuple(uint256_to_bytes(head_length + offset) for offset in tail_offsets)
            raw_head_chunks.append(None)
            tail_chunks.append(encoded_size + b"".join(head_chunks + tmp_tail_chunks))
        elif tp == "(address,bytes)":
            encoded_size = uint256_to_bytes(len(value))
            encoded_elements = b""
            for target, call_data in value:
                encoded_elements += pad_address(target)
                encoded_elements += tuple_encode([call_data], ["bytes"])
            raw_head_chunks.append(None)
            tail_chunks.append(encoded_size + encoded_elements)
        else:
            raise Exception(f"Unsupported type {tp}")

    head_length = sum(32 if item is None else len(item) for item in raw_head_chunks)
    tail_offsets = (0,) + tuple(accumulate(map(len, tail_chunks[:-1])))
    head_chunks = tuple(
        uint256_to_bytes(head_length + offset) if chunk is None else chunk
        for chunk, offset in zip(raw_head_chunks, tail_offsets)
    )

    encoded_value = b"".join(head_chunks + tuple(tail_chunks))
    return encoded_value
