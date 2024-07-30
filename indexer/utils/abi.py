from typing import Sequence, Any, Optional, Tuple
from urllib.parse import to_bytes

from eth_abi.codec import ABICodec
from eth_abi.grammar import BasicType
from eth_typing import HexStr, TypeStr, ChecksumAddress
from eth_utils import to_hex, encode_hex, text_if_str, to_text, hexstr_if_str, is_binary_address
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.abi import get_abi_input_types, build_strict_registry, map_abi_data
from web3._utils.normalizers import implicitly_identity, parse_basic_type_str
from web3.types import ABIFunction

codec = ABICodec(build_strict_registry())


@implicitly_identity
def abi_string_to_text(type_str: TypeStr, data: Any) -> Optional[Tuple[TypeStr, str]]:
    if type_str == "string":
        return type_str, text_if_str(to_text, data)
    return None


@implicitly_identity
@parse_basic_type_str
def abi_bytes_to_bytes(
        abi_type: BasicType, type_str: TypeStr, data: Any
) -> Optional[Tuple[TypeStr, HexStr]]:
    if abi_type.base == "bytes" and not abi_type.is_array:
        return type_str, hexstr_if_str(to_bytes, data)
    return None


@implicitly_identity
def abi_address_to_hex(
        type_str: TypeStr, data: Any
) -> Optional[Tuple[TypeStr, ChecksumAddress]]:
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
