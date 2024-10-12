#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/12 下午2:13
Author  : xuzh
Project : hemera_indexer
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

import eth_abi
from eth_abi.codec import ABICodec
from web3._utils.abi import exclude_indexed_event_inputs, get_indexed_event_inputs, named_tree
from web3.types import ABIEvent, ABIFunction

from indexer.domain.log import Log
from indexer.utils.abi import event_log_abi_to_topic, function_abi_to_4byte_selector_str, get_types_from_abi_type_list


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


def decode_log_ignore_indexed(
    fn_abi: ABIEvent,
    log: Log,
) -> Optional[Dict[str, Any]]:
    data_types = get_indexed_event_inputs(fn_abi) + exclude_indexed_event_inputs(fn_abi)
    abi_codec = ABICodec(eth_abi.registry.registry)
    decoded_data = abi_codec.decode([t["type"] for t in data_types], log.get_topic_with_data())
    data = named_tree(data_types, decoded_data)
    return data


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
        decode_indexed = abi_codec.decode(get_types_from_abi_type_list(indexed_types), log.get_bytes_topics())
        indexed = named_tree(indexed_types, decode_indexed)

        decoded_data = abi_codec.decode(get_types_from_abi_type_list(data_types), log.get_bytes_data())
        data = named_tree(data_types, decoded_data)
    except Exception as e:
        logging.warning(f"Failed to decode log: {e}, log: {log}")
        return None

    return {**indexed, **data}


class Function:
    def __init__(self, function_abi: ABIFunction):
        self._function_abi = function_abi
        self._signature = function_abi_to_4byte_selector_str(function_abi)
        self._inputs_type = [_input["type"] for _input in self._function_abi["inputs"]]
        self._outputs_type = [_output["type"] for _output in self._function_abi["outputs"]]

    def get_abi(self) -> ABIFunction:
        return self._function_abi

    def get_signature(self) -> str:
        return self._signature

    def get_inputs_type(self) -> List[str]:
        return self._inputs_type

    def get_outputs_type(self) -> List[str]:
        return self._outputs_type


def analyze_abi(abi_info: Union[List[dict], str]) -> Dict[Any, Union[Function, Event]]:
    abi_struct = {}

    if isinstance(abi_info, str):
        abi_info = json.loads(abi_info)

    for abi in abi_info:
        if abi["type"] == "function":
            abi_struct[abi["name"]] = Function(abi)
        elif abi["type"] == "event":
            abi_struct[abi["name"]] = Event(abi)

    return abi_struct
