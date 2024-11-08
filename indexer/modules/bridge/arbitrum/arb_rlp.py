#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/9 10:36
# @Author  will
# @File  arb_rlp.py
# @Brief

import rlp
from web3 import Web3

from common.utils.format_utils import hex_str_to_bytes


def convert_int_bytes(value, length):
    if isinstance(value, bytes):
        return value
    return value.to_bytes(length, byteorder="big")


def calculate_submit_retryable_id(
    l2_chain_id,
    message_number,
    from_address,
    l1_base_fee,
    dest_address,
    l2_call_value,
    l1_value,
    max_submission_fee,
    excess_fee_refund_address,
    call_value_refund_address,
    gas_limit,
    max_fee_per_gas,
    data,
):
    r_dest_address = dest_address if dest_address != "0x0000000000000000000000000000000000000000" else "0x"
    fields = [
        l2_chain_id,
        convert_int_bytes(message_number, 32),
        hex_str_to_bytes(from_address),
        l1_base_fee,
        l1_value,
        max_fee_per_gas,
        gas_limit,
        hex_str_to_bytes(r_dest_address),
        l2_call_value,
        hex_str_to_bytes(call_value_refund_address),
        max_submission_fee,
        hex_str_to_bytes(excess_fee_refund_address),
        hex_str_to_bytes(data),
    ]
    encoded_data = rlp.encode(fields)
    mm = b"\x69" + encoded_data
    return Web3.keccak(hexstr=(Web3.to_hex(mm))).hex()


def calculate_deposit_tx_id(l2_chain_id, message_number, from_address, to_address, value):
    fields = [
        l2_chain_id,
        convert_int_bytes(message_number, 32),
        hex_str_to_bytes(from_address),
        hex_str_to_bytes(to_address),
        value,
    ]

    encoded_data = rlp.encode(fields)
    mm = b"\x64" + encoded_data
    return Web3.keccak(hexstr=(Web3.to_hex(mm))).hex()


if __name__ == "__main__":
    pass
