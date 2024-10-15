#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/12 下午2:13
Author  : xuzh
Project : hemera_indexer
"""
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

import eth_abi
from ens.utils import get_abi_output_types
from eth_abi import abi
from eth_abi.codec import ABICodec
from eth_typing import HexStr
from eth_utils import encode_hex, to_hex
from hexbytes import HexBytes
from web3._utils.abi import (
    exclude_indexed_event_inputs,
    get_abi_input_types,
    get_indexed_event_inputs,
    map_abi_data,
    named_tree,
)
from web3._utils.contracts import decode_transaction_data
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3.types import ABIEvent, ABIFunction

from common.utils.format_utils import bytes_to_hex_str, convert_bytes_to_hex, convert_dict, hex_str_to_bytes
from indexer.utils.abi import (
    abi_address_to_hex,
    abi_bytes_to_bytes,
    abi_string_to_text,
    codec,
    event_log_abi_to_topic,
    function_abi_to_4byte_selector_str,
    get_types_from_abi_type_list,
)

abi_codec = ABICodec(eth_abi.registry.registry)


class Event:
    def __init__(self, event_abi: ABIEvent):
        self._event_abi = event_abi
        self._signature = event_log_abi_to_topic(event_abi)

    def get_abi(self) -> ABIEvent:
        return self._event_abi

    def get_signature(self) -> str:
        return self._signature

    def decode_log(self, log) -> Optional[Dict[str, Any]]:
        return decode_log(self._event_abi, log)

    def decode_log_ignore_indexed(self, log) -> Optional[Dict[str, Any]]:
        return decode_log_ignore_indexed(self._event_abi, log)


def decode_log_ignore_indexed(
    fn_abi: ABIEvent,
    log,
) -> Optional[Dict[str, Any]]:
    from indexer.domain.log import Log

    if not isinstance(log, Log):
        raise ValueError(f"log: {log} is not a Log instance")

    data_types = get_indexed_event_inputs(fn_abi) + exclude_indexed_event_inputs(fn_abi)
    decoded_data = decode_data([t["type"] for t in data_types], log.get_topic_with_data())
    data = named_tree(data_types, decoded_data)
    return data


def decode_log(
    fn_abi: ABIEvent,
    log,
) -> Optional[Dict[str, Any]]:
    from indexer.domain.log import Log

    if not isinstance(log, Log):
        raise ValueError(f"log: {log} is not a Log instance")

    try:
        indexed_types = get_indexed_event_inputs(fn_abi)
        for indexed_type in indexed_types:
            if indexed_type["type"] == "string":
                indexed_type["type"] = "bytes32"

        data_types = exclude_indexed_event_inputs(fn_abi)

        decode_indexed = decode_data(get_types_from_abi_type_list(indexed_types), log.get_bytes_topics())
        indexed = named_tree(indexed_types, decode_indexed)

        decoded_data = decode_data(get_types_from_abi_type_list(data_types), log.get_bytes_data())
        data = named_tree(data_types, decoded_data)
    except Exception as e:
        logging.warning(f"Failed to decode log: {e}, log: {log}")
        return None

    return {**indexed, **data}


class Function:
    def __init__(self, function_abi: ABIFunction):
        self._function_abi = function_abi
        self._signature = function_abi_to_4byte_selector_str(function_abi)
        self._inputs_type = get_abi_input_types(function_abi)
        self._outputs_type = get_abi_output_types(function_abi)

    def get_abi(self) -> ABIFunction:
        return self._function_abi

    def get_signature(self) -> str:
        return self._signature

    def get_inputs_type(self) -> List[str]:
        return self._inputs_type

    def get_outputs_type(self) -> List[str]:
        return self._outputs_type

    def decode_data(self, data: str) -> Optional[Dict[str, Any]]:
        try:
            decoded = decode_data(self._inputs_type, hex_str_to_bytes(data)[4:])
            decoded = named_tree(self._function_abi["inputs"], decoded)
            return decoded
        except Exception as e:
            logging.warning(f"Failed to decode transaction input data: {e}, input data: {data}")
            return None


def decode_transaction_data(
    fn_abi: ABIFunction,
    data: str,
) -> Optional[Dict[str, Any]]:
    try:
        types = get_abi_input_types(fn_abi)
        decoded = decode_data(types, hex_str_to_bytes(data[4:]))
        decoded = named_tree(fn_abi["inputs"], decoded)
        return decoded
    except Exception as e:
        logging.warning(f"Failed to decode transaction input data: {e}, input data: {data}")
        return None


def decode_data(decode_type: Union[Sequence[str], List[str], str], data: bytes) -> Tuple[Any, ...]:
    if isinstance(decode_type, str):
        data = abi_codec.decode([decode_type], data)
    elif isinstance(decode_type, list):
        for tpe in decode_type:
            if not isinstance(tpe, str):
                raise ValueError(f"Invalid decode_type: {decode_type} is not a List[str]")
        try:
            data = abi_codec.decode(decode_type, data)
        except Exception as e:
            print(f"Failed to decode data: {e}")
    else:
        raise ValueError(f"Invalid decode_type: {decode_type}, it should be str or list[str]")
    return data


def encode_data(
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


def decode_log_data(types, data_str):
    data_hex_str = hex_str_to_bytes(data_str)
    decoded_abi = decode_data(types, data_hex_str)

    encoded_abi = []
    decoded_abi_real = []
    for index in range(len(types)):
        encoded_abi.append(bytes_to_hex_str(abi.encode(types[index : index + 1], decoded_abi[index : index + 1])))

        if types[index].startswith("byte"):
            if type(decoded_abi[index]) is tuple:
                encode_tuple = []
                for element in decoded_abi[index]:
                    encode_tuple.append(bytes_to_hex_str(element))
                decoded_abi_real.append(encode_tuple)
            else:
                decoded_abi_real.append(bytes_to_hex_str(decoded_abi[index]))
        else:
            decoded_abi_real.append(str(decoded_abi[index]))

    return decoded_abi_real, encoded_abi


def decode_function(function_abi_json, data_str, output_str):
    if data_str is not None and len(data_str) > 0:
        input = decode_transaction_data(
            cast(ABIFunction, function_abi_json),
            data_str,
            normalizers=BASE_RETURN_NORMALIZERS,
        )
        input = convert_dict(convert_bytes_to_hex(input))
    else:
        input = []

    if output_str is not None and len(output_str) > 0:
        types = get_abi_output_types(cast(ABIFunction, function_abi_json))
        data = hex_str_to_bytes(output_str)
        value = decode_data(types, data)
        output = named_tree(function_abi_json["outputs"], value)
        output = convert_dict(convert_bytes_to_hex(output))
    else:
        output = []
    return input, output
