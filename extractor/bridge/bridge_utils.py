import json
from typing import Optional, Tuple

from eth_utils import to_int

from domain.transaction import format_transaction_data
from extractor.types import Log, Receipt, Transaction
from utils.json_rpc_requests import generate_get_block_by_number_json_rpc, generate_get_receipt_json_rpc
from utils.provider import BatchHTTPProvider
from utils.utils import rpc_response_batch_to_results


def get_version_and_index_from_nonce(nonce: int) -> (int, int):
    version = nonce >> 240
    index = nonce & int("0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", 16)
    return (version, index)


def unmarshal_deposit_version1(opaque_data: bytes) -> Tuple[Optional[int], int, int, int, int, bool, bytes]:
    assert len(opaque_data) >= 32 + 32 + 32 + 32 + 8 + 1, f"Unexpected opaqueData length: {len(opaque_data)}"
    offset = 0

    # uint256 mint
    mint = int.from_bytes(opaque_data[offset : offset + 32], "big")
    mint_option = None if mint == 0 else mint
    offset += 32

    # uint256 value
    value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint256 ethValue
    eth_value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint256 ethTxValue
    eth_tx_value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint64 gas
    gas = int.from_bytes(opaque_data[offset : offset + 8], "big")
    assert gas.bit_length() <= 64, "Bad gas value"
    offset += 8

    # uint8 isCreation
    is_creation = opaque_data[offset] == 1
    offset += 1

    # remaining bytes fill the data
    tx_data = opaque_data[offset:]

    return mint_option, value, eth_value, eth_tx_value, gas, is_creation, tx_data


def unmarshal_deposit_version0(opaque_data: bytes) -> Tuple[Optional[int], int, int, bool, bytes]:
    assert len(opaque_data) >= 32 + 32 + 8 + 1, f"Unexpected opaqueData length: {len(opaque_data)}"
    offset = 0

    # uint256 mint
    mint = int.from_bytes(opaque_data[offset : offset + 32], "big")
    mint_option = None if mint == 0 else mint
    offset += 32

    # uint256 value
    value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint64 gas
    gas = int.from_bytes(opaque_data[offset : offset + 8], "big")
    assert gas.bit_length() <= 64, "Bad gas value"
    offset += 8

    # uint8 isCreation
    is_creation = opaque_data[offset] == 1
    offset += 1

    # transaction data
    tx_data = opaque_data[offset:]

    return mint_option, value, gas, is_creation, tx_data
