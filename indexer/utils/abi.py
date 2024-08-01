from typing import Any, Dict, Optional, Sequence, Tuple
from urllib.parse import to_bytes

import eth_abi
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
    to_hex,
    to_text,
)
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.abi import (
    build_strict_registry,
    exclude_indexed_event_inputs,
    get_abi_input_types,
    get_indexed_event_inputs,
    map_abi_data,
    named_tree,
)
from web3._utils.normalizers import implicitly_identity, parse_basic_type_str
from web3.types import ABIEvent, ABIFunction

from indexer.domain.log import Log

codec = ABICodec(build_strict_registry())
import eth_abi.registry


def bytes_to_hex_str(b: bytes) -> str:
    return "0x" + b.hex()


def event_log_abi_to_topic(event_abi: ABIEvent) -> str:
    return "0x" + event_abi_to_log_topic(event_abi).hex()


def function_abi_to_4byte_selector_str(function_abi: ABIFunction) -> str:
    # return 10 hex string
    return "0x" + function_abi_to_4byte_selector(function_abi).hex()


def decode_log(
    fn_abi: ABIEvent,
    log: Log,
) -> Optional[Dict[str, Any]]:
    try:
        indexed_types = get_indexed_event_inputs(fn_abi)
        for indexed_type in indexed_types:
            if indexed_type["type"] == "string":
                indexed_type["type"] = "bytes32"

        data_types = exclude_indexed_event_inputs(fn_abi)

        abi_codec = ABICodec(eth_abi.registry.registry)
        decode_indexed = abi_codec.decode([t["type"] for t in indexed_types], log.get_bytes_topics())
        indexed = named_tree(indexed_types, decode_indexed)

        decoded_data = abi_codec.decode([t["type"] for t in data_types], log.get_bytes_data())
        data = named_tree(data_types, decoded_data)
    except Exception as e:
        print(e)
        raise e

    return {**indexed, **data}


def decode_log_ignore_indexed(
    fn_abi: ABIEvent,
    log: Log,
) -> Optional[Dict[str, Any]]:
    data_types = get_indexed_event_inputs(fn_abi) + exclude_indexed_event_inputs(fn_abi)
    abi_codec = ABICodec(eth_abi.registry.registry)
    decoded_data = abi_codec.decode([t["type"] for t in data_types], log.get_topic_with_data())
    data = named_tree(data_types, decoded_data)
    return data


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


class Event:
    def __init__(self, event_abi: ABIEvent):
        self._event_abi = event_abi
        self._signature = event_log_abi_to_topic(event_abi)

    def get_signature(self) -> str:
        return self._signature

    def decode_log(self, log: Log) -> Optional[Dict[str, Any]]:
        return decode_log(self._event_abi, log)

    def decode_log_ignore_indexed(self, log: Log) -> Optional[Dict[str, Any]]:
        return decode_log_ignore_indexed(self._event_abi, log)
