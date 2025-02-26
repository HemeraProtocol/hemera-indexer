import base64
import json
import re
from optparse import Option
from typing import Optional

import requests
from web3 import Web3

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

SUPPORT_CHAINS = {
    "ethereum": {
        "display_name": "Ethereum",
        "rpc": "https://cloudflare-eth.com",
        "etherscan_address_link": "https://etherscan.io/address/",
        "explorer_transaction_link": "https://etherscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 1,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "arbitrum": {
        "display_name": "Arbitrum",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "etherscan_address_link": "https://arbiscan.io/address/",
        "explorer_transaction_link": "https://arbiscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 42161,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "optimism": {
        "display_name": "Optimism",
        "rpc": "https://mainnet.optimism.io",
        "etherscan_address_link": "https://optimistic.etherscan.io/address/",
        "explorer_transaction_link": "https://optimistic.etherscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 10,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "base": {
        "display_name": "Base",
        "rpc": "https://mainnet.base.org",
        "etherscan_address_link": "https://basescan.org/address/",
        "explorer_transaction_link": "https://basescan.org/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 8453,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "linea": {
        "display_name": "Linea",
        "rpc": "https://rpc.linea.build",
        "etherscan_address_link": "https://lineascan.build/address/",
        "explorer_transaction_link": "https://lineascan.build/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 59144,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "mantle": {
        "display_name": "Mantle",
        "rpc": "https://rpc.mantle.xyz",
        "etherscan_address_link": "https://explorer.mantle.xyz/address/",
        "explorer_transaction_link": "https://explorer.mantle.xyz/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "MNT",
        "chain_id": 5000,
        "coin": {
            "symbol": "MNT",
            "id": 27075,
        },
    },
}

chain_id_name_mapping = {SUPPORT_CHAINS[chain_name]["chain_id"]: chain_name for chain_name in SUPPORT_CHAINS.keys()}


def build_web3(provider):
    w3 = Web3(provider)
    w3.middleware_onion.inject(PythonicMiddleware, layer=0)
    return w3


def verify_0_address(address):
    return set(address[2:]) == {"0"}


def get_debug_trace_transaction(traces):
    def prune_delegates(trace):
        while (
            trace.get("calls") and len(trace.get("calls")) == 1 and trace.get("calls")[0]["call_type"] == "delegatecall"
        ):
            trace = trace["calls"][0]
        if trace.get("calls"):
            for i, sub_call in enumerate(trace.get("calls")):
                trace["calls"][i] = prune_delegates(sub_call)

        return trace

    def promote_delegate_calls(node, parent=None, index=None):
        if "calls" in node:
            for i, sub_node in enumerate(node["calls"]):
                if sub_node:
                    promote_delegate_calls(sub_node, node, i)

        if node.get("call_type") == "delegatecall" and node.get("already_promoted") != True and parent is not None:
            parent.update(
                {
                    "delegate_address": parent["from"],
                    "already_promoted": True,
                }
            )
            parent["calls"][index] = {}

    def parse_trace_address(trace_address):
        if trace_address == "{}":
            return []
        return list(map(int, trace_address.strip("{}").split(",")))

    def add_trace_to_tree(node, trace, path):
        for step in path:
            if "calls" not in node:
                node["calls"] = []
            if len(node["calls"]) <= step:
                node["calls"].extend([{}] * (step + 1 - len(node["calls"])))
            node = node["calls"][step]

        node.update(trace)
        node["trace_address"] = path

    root = {}
    for trace in traces:
        path = parse_trace_address(trace["trace_address"])
        add_trace_to_tree(root, trace, path)

    return prune_delegates(root)


def generate_type_str(component):
    if component["type"] == "tuple[]":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")[]"
    elif component["type"] == "tuple":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")"
    else:
        return component["type"]


def is_eth_address(address):
    return Web3.is_address(address)


def is_eth_transaction_hash(hash):
    pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
    return bool(re.fullmatch(pattern, hash))


def valid_hash(value: str) -> Optional[str]:
    """Check if the input string is a valid block hash.

    Args:
        value: Input string to validate

    Returns:
        bool: True if the input is a valid block hash, False otherwise

    Examples:
        >>> valid_hash("0x1234...")  # 64 hex chars with 0x prefix
        True
        >>> valid_hash("1234...")    # 64 hex chars without prefix
        True
        >>> valid_hash("0xabcd")     # Too short
        False
    """
    # Remove 0x prefix if present
    hex_value = value.lower().removeprefix("0x")

    # Check if the string has exactly 64 characters (32 bytes)
    if len(hex_value) != 64:
        return None

    # Check if all characters are valid hex digits
    try:
        int(hex_value, 16)
        return "0x" + hex_value.lower()
    except ValueError:
        return None


def to_checksum_address(address):
    return Web3.to_checksum_address(address)


def decode_data_url_to_json(data_url):
    mime, encoded_data = data_url.split(",", 1)
    if ";base64" in mime:
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
    else:
        decoded_data = encoded_data
    try:
        return json.loads(decoded_data)
    except Exception as e:
        print(e)
        return None


def http_transfer_uri(uri):
    if uri.startswith("ipfs"):
        return "https://ipfs.io/ipfs/" + uri[7:]
    elif uri.startswith("http"):
        return uri
    else:
        return None


def get_json_from_uri_by_http(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def event_topic_to_address(topic: str) -> str:
    if len(topic) != 66:
        return ""
    return Web3.to_checksum_address("0x" + topic[26:])


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()
