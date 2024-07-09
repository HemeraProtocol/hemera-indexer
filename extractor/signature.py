from typing import Dict, Any, Optional

import eth_abi.registry
from eth_abi.codec import ABICodec
from eth_utils import function_abi_to_4byte_selector, event_abi_to_log_topic
from web3._utils.abi import get_indexed_event_inputs, exclude_indexed_event_inputs, named_tree
from web3.types import ABIEvent,ABIFunction

from extractor.types import Log


def bytes_to_hex_str(b: bytes) -> str:
    return '0x' + b.hex()

def event_log_abi_to_topic(event_abi: ABIEvent) -> str:
    return '0x' + event_abi_to_log_topic(event_abi).hex()


def function_abi_to_4byte_selector_str(function_abi: ABIFunction) -> str:
    # return 10 hex string
    return '0x' + function_abi_to_4byte_selector(function_abi).hex()


def decode_log(
        fn_abi: ABIEvent,
        log: Log,
) -> Optional[Dict[str, Any]]:
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

    return {**indexed, **data}
