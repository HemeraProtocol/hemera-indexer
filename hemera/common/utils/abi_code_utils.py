#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/12 下午2:13
Author  : xuzh
Project : hemera_indexer
"""
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import eth_abi
from ens.utils import get_abi_output_types
from eth_abi import abi
from eth_abi.codec import ABICodec
from eth_typing import TypeStr
from eth_utils import encode_hex, to_hex
from hexbytes import HexBytes
from web3._utils.abi import (
    exclude_indexed_event_inputs,
    get_abi_input_types,
    get_indexed_event_inputs,
    map_abi_data,
    named_tree,
)
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3.types import ABIEvent, ABIFunction

from hemera.common.utils.exception_control import FastShutdownError
from hemera.common.utils.format_utils import bytes_to_hex_str, convert_bytes_to_hex, convert_dict, hex_str_to_bytes
from hemera.indexer.domains.log import Log
from hemera.indexer.utils.abi import (
    abi_address_to_hex,
    abi_bytes_to_bytes,
    abi_string_to_text,
    codec,
    event_log_abi_to_topic,
    function_abi_to_4byte_selector_str,
    get_types_from_abi_type_list,
    pad_address,
    uint256_to_bytes,
)

abi_codec = ABICodec(eth_abi.registry.registry)


class Event:

    def __init__(self, event_abi: ABIEvent):
        """
        Initializes an Event object.

        :param event_abi: The ABI (Application Binary Interface) of the event.
        :type event_abi: ABIEvent
        """
        self._event_abi = event_abi
        self._signature = event_log_abi_to_topic(event_abi)

    def get_abi(self) -> ABIEvent:
        """
        Returns the ABI of the Event.

        :return: The event's ABI.
        :rtype: ABIEvent
        """
        return self._event_abi

    def get_signature(self) -> str:
        """
        Returns the signature of the event.

        :return: The event signature.
        :rtype: str
        """
        return self._signature

    def get_name(self) -> str:
        return self._event_abi["name"]

    def decode_log(self, log) -> Optional[Dict[str, Any]]:
        """
        Decodes the given log using the event ABI.

        :param log: The log to decode.
        :type log: Log

        :return: A dictionary containing the decoded log data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        return decode_log(self._event_abi, log)

    def decode_log_ignore_indexed(self, log) -> Optional[Dict[str, Any]]:
        """
        Decodes the given log, ignoring indexed parameters.

        :param log: The log to decode.
        :type log: Log

        :return: A dictionary containing the decoded log data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        return decode_log_ignore_indexed(self._event_abi, log)


def decode_log_ignore_indexed(
    fn_abi: ABIEvent,
    log,
) -> Optional[Dict[str, Any]]:
    """
    Decodes a log, ignoring indexed parameters.

    :param fn_abi: The ABI of the event function.
    :type fn_abi: ABIEvent

    :param log: The log to decode.
    :type log: Log

    :return: A dictionary containing the decoded log data, or raise exception if decoding fails.
    :rtype: Optional[Dict[str, Any]]
    """
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
    """
    Decodes a log, including indexed parameters.

    :param fn_abi: The ABI of the event function.
    :type fn_abi: ABIEvent

    :param log: The log to decode.
    :type log: Log

    :return: A dictionary containing the decoded log data, or None if decoding fails.
    :rtype: Optional[Dict[str, Any]]
    """

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
        """
        Initializes a Function object.

        :param function_abi: The ABI of the function.
        :type function_abi: ABIFunction
        """
        self._function_abi = function_abi
        self._signature = function_abi_to_4byte_selector_str(function_abi)
        self._inputs_type = get_abi_input_types(function_abi)
        self._outputs_type = get_abi_output_types(function_abi)

    def get_abi(self) -> ABIFunction:
        """
        Returns the ABI of the function.

        :return: The function's ABI.
        :rtype: ABIFunction
        """
        return self._function_abi

    def get_signature(self) -> str:
        """
        Returns the signature of the function.

        :return: The function's signature.
        :rtype: str
        """
        return self._signature

    def get_name(self) -> str:
        return self.get_abi()["name"]

    def get_inputs_type(self) -> List[str]:
        """
        Returns the list of input types for the function.

        :return: A list of input types.
        :rtype: List[str]
        """
        return self._inputs_type

    def get_outputs_type(self) -> List[str]:
        """
        Returns the list of output types for the function.

        :return: A list of output types.
        :rtype: List[str]
        """
        return self._outputs_type

    def decode_function_input_data(
        self,
        data: str,
        normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Decodes the input data for the function.

        :param data: The input data to decode.
        :type data: str

        :param normalizers: An optional sequence of callable normalizers. Each normalizer
                        should take a type string and a value, and return a tuple of
                        the (potentially modified) type string and value.
        :type normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]]

        :return: A dictionary containing the decoded data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        if self._signature != data[:10]:
            raise FastShutdownError(f"Input data is not compare to {self._function_abi['name']} ABI.")

        try:
            decoded = decode_data(self._inputs_type, hex_str_to_bytes(data)[4:])
            if normalizers:
                decoded = map_abi_data(normalizers, self._inputs_type, decoded)
            decoded = named_tree(self._function_abi["inputs"], decoded)
            return decoded
        except Exception as e:
            logging.warning(f"Failed to decode transaction input data: {e}, input data: {data}")
            return None

    def decode_function_output_data(
        self,
        data: str,
        normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Decodes the output data for the function.

        :param data: The output data to decode.
        :type data: str

        :param normalizers: An optional sequence of callable normalizers. Each normalizer
                        should take a type string and a value, and return a tuple of
                        the (potentially modified) type string and value.
        :type normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]]

        :return: A dictionary containing the decoded data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            decoded = decode_data(self._outputs_type, hex_str_to_bytes(data))
            if normalizers:
                decoded = map_abi_data(normalizers, self._inputs_type, decoded)
            decoded = named_tree(self._function_abi["outputs"], decoded)
            return decoded
        except Exception as e:
            logging.warning(f"Failed to decode transaction output data: {e}, input data: {data}")
            return None

    def encode_function_call_data(self, arguments: Sequence[Any]) -> str:
        """
        Encodes the function call data.

        :param arguments: The arguments to encode.
        :type arguments: Sequence[Any]

        :param data: Additional data to prepend to the encoded arguments (optional).
        :type data: str

        :return: The encoded function call data as a hexadecimal string.
        :rtype: str
        """
        if arguments is None:
            arguments = []

        if len(arguments) != len(self._inputs_type):
            raise ValueError(f"Expected {len(self._inputs_type)} arguments, got {len(arguments)}")

        if len(arguments) > 2:
            return encode_data(self._function_abi, arguments, self.get_signature())

        encoded = hex_str_to_bytes(self._signature)
        for arg, arg_type in zip(arguments, self._inputs_type):
            if arg_type == "address":
                encoded += pad_address(arg)
            elif arg_type == "uint256":
                encoded += uint256_to_bytes(arg)
            else:
                # cannot handle, call encode directly
                return encode_data(self._function_abi, arguments, self.get_signature())
        return bytes_to_hex_str(encoded)


class FunctionCollection:
    def __init__(self, functions: List[Function]):
        """
        Initializes a FunctionCollection object.

        :param functions: A list of Function objects.
        :type functions: List[Function]
        """
        self._functions = functions
        self._function_map = {function.get_signature(): function for function in functions}

    def get_function_by_signature(self, signature: str) -> Optional[Function]:
        """
        Returns a Function object by its signature.

        :param signature: The signature of the function.
        :type signature: str

        :return: The Function object if found, otherwise None.
        :rtype: Optional[Function]
        """
        for function in self._functions:
            if function.get_signature() == signature:
                return function
        return None

    def get_functions(self) -> List[Function]:
        """
        Returns the list of Function objects.

        :return: A list of Function objects.
        :rtype: List[Function]
        """
        return self._functions

    def decode_function_input_data(self, data: str) -> Optional[Dict[str, Any]]:
        """
        Decodes the input data for a function given its signature.

        :param signature: The signature of the function.
        :type signature: str

        :param data: The input data to decode.
        :type data: str

        :return: A dictionary containing the decoded data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        signature = data[:10]
        if signature not in self._function_map:
            logging.warning(f"Function signature {signature} not found in function map.")
            return None
        function = self._function_map[signature]
        return function.decode_function_input_data(data)


def decode_transaction_data(
    fn_abi: ABIFunction,
    data: str,
    normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Decodes transaction input data.

    :param fn_abi: The ABI of the function.
    This function attempts to decode the input data of a transaction using the specified
    function ABI. It can optionally apply normalizers to the decoded data.

    :param fn_abi: The ABI (Application Binary Interface) of the function.
    :type fn_abi: ABIFunction

    :param data: The input data to decode. This should be a hexadecimal string
                 representing the entire input data of the transaction, including
                 the 4-byte function selector.
    :type data: str

    :param normalizers: An optional sequence of callable normalizers. Each normalizer
                        should take a type string and a value, and return a tuple of
                        the (potentially modified) type string and value.
    :type normalizers: Sequence[Callable[[TypeStr, Any], Tuple[TypeStr, Any]]]

    :return: A dictionary containing the decoded data, where keys are parameter names
             and values are the decoded values. Returns None if decoding fails.
    :rtype: Optional[Dict[str, Any]]

    :raises Exception: If there's an error during the decoding process. The exception
                       is caught and logged, and the function returns None.

    Note:
    - The function assumes that the first 4 bytes of the input data are the function
      selector, and it decodes only the data after these 4 bytes.
    - If decoding fails, a warning is logged with the error message and the input data.
    """
    try:
        types = get_abi_input_types(fn_abi)
        decoded = decode_data(types, hex_str_to_bytes(data)[4:])
        if normalizers:
            decoded = map_abi_data(normalizers, types, decoded)
        decoded = named_tree(fn_abi["inputs"], decoded)
        return decoded
    except Exception as e:
        logging.warning(f"Failed to decode transaction input data: {e}, input data: {data}")
        return None


def decode_data(decode_type: Union[Sequence[str], List[str], str], data: bytes) -> Tuple[Any, ...]:
    """
    Decodes data based on the given type(s).

    :param decode_type: The type(s) to use for decoding.
    :type decode_type: Union[Sequence[str], List[str], str]

    :param data: The data to decode.
    :type data: bytes

    :return: A tuple containing the decoded data.
    :rtype: Tuple[Any, ...]

    :raises ValueError: If the decode_type is invalid.
    """
    if isinstance(decode_type, str):
        data = abi_codec.decode([decode_type], data)
    elif isinstance(decode_type, list):
        for tpe in decode_type:
            if not isinstance(tpe, str):
                raise ValueError(f"Invalid decode_type: {decode_type} is not a List[str]")
        try:
            data = abi_codec.decode(decode_type, data)
        except Exception as e:
            logging.warning(f"Failed to decode data: {e}")
            return None
    else:
        raise ValueError(f"Invalid decode_type: {decode_type}, it should be str or list[str]")
    return data


def encode_data(
    abi: ABIFunction,
    arguments: Sequence[Any],
    data: str = None,
) -> str:
    """
    Encodes function call data.

    :param abi: The ABI of the function.
    :type abi: ABIFunction

    :param arguments: The arguments to encode.
    :type arguments: Sequence[Any]

    :param data: Additional data to prepend to the encoded arguments (optional).
    :type data: str

    :return: The encoded function call data as a hexadecimal string.
    :rtype: str
    """
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


def decode_log_data(types: List[str], data_str: str) -> Tuple[List[Union[str, List[str]]], List[str]]:
    """
    Decodes log data based on the provided types and returns both decoded and encoded versions.
    This function takes a list of ABI types and a data string, decodes the data, and then
    re-encodes each element. It handles special cases for byte types.

    :param types: A list of ABI type strings representing the structure of the data.
    :type types: List[str]

    :param data_str: The data to be decoded, typically in hexadecimal string format.
    :type data_str: str

    :return: A tuple containing two lists:
             1. decoded_abi_real: A list of decoded values, where byte types are converted to hex strings.
             2. encoded_abi: A list of re-encoded values in hexadecimal string format.
    :rtype: Tuple[List[Union[str, List[str]]], List[str]]

    Note:
    - The function first decodes the entire data string using the provided types.
    - It then processes each decoded element individually:
      - For byte types, it converts the decoded value(s) to hexadecimal string(s).
      - For other types, it converts the decoded value to a string.
    - The function also re-encodes each element individually and stores the result.
    - Special handling is implemented for byte types that result in tuples (likely representing arrays or structs).

    This function is particularly useful for processing and analyzing blockchain log data,
    allowing for both human-readable output (decoded_abi_real) and data that can be used
    for further on-chain interactions (encoded_abi).
    """
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


def decode_function(abi_function: Function, data_str: str, output_str: str):
    """
    Decodes both the input and output data of a function call using the provided ABI function.
    This function handles the decoding of both input data (function arguments) and output data
    (function return values) for a given function call. It can process cases where either input
    or output data (or both) are provided.

    :param abi_function: An instance of the Function class representing the ABI of the function.
    :type abi_function: Function

    :param data_str: The input data string to be decoded. This typically represents the function
                     arguments. Can be None or an empty string if no input data is available.
    :type data_str: str

    :param output_str: The output data string to be decoded. This typically represents the
                       function's return value(s). Can be None or an empty string if no output
                       data is available.
    :type output_str: str

    :return: A tuple containing two elements:
             1. input: Decoded input data as a dictionary (if present) or an empty list.
             2. output: Decoded output data as a dictionary (if present) or an empty list.
    :rtype: Tuple[Union[List, Dict], Union[List, Dict]]

    Note:
    - For input data:
      - If provided, it's decoded using the function's ABI and normalized.
      - The result is converted to use hexadecimal strings for byte values.
    - For output data:
      - If provided, it's decoded based on the function's output types.
      - The decoded values are associated with their respective output names.
      - The result is converted to use hexadecimal strings for byte values.
    - If either input or output data is not provided or empty, an empty list is returned
      for that part.

    This function is particularly useful for analyzing and debugging smart contract function
    calls, allowing easy interpretation of both the input arguments and return values.
    """
    if data_str is not None and len(data_str) > 0:
        input = abi_function.decode_function_input_data(data_str, normalizers=BASE_RETURN_NORMALIZERS)
        input = convert_dict(convert_bytes_to_hex(input))
    else:
        input = []

    if output_str is not None and len(output_str) > 0:
        output = abi_function.decode_function_output_data(output_str)
        output = convert_dict(convert_bytes_to_hex(output))
    else:
        output = []
    return input, output
