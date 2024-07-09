#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/9 10:36
# @Author  will
# @File  arb_util.py
# @Brief
import hashlib

import rlp
from eth_abi import abi
from web3 import Web3


def convert_int_bytes(value, length):
    if isinstance(value, bytes):
        return value
    return value.to_bytes(length, byteorder='big')


def calculate_submit_retryable_id(l2_chain_id, message_number, from_address, l1_base_fee,
                                  dest_address, l2_call_value, l1_value, max_submission_fee,
                                  excess_fee_refund_address, call_value_refund_address,
                                  gas_limit, max_fee_per_gas, data):
    r_dest_address = dest_address if dest_address != "0x0000000000000000000000000000000000000000" else "0x"
    fields = [
        (l2_chain_id),
        convert_int_bytes(message_number, 32),
        bytes.fromhex(from_address[2:]),
        (l1_base_fee),
        (l1_value),
        (max_fee_per_gas),
        (gas_limit),
        bytes.fromhex(r_dest_address[2:]),
        (l2_call_value),
        bytes.fromhex(call_value_refund_address[2:]),
        (max_submission_fee),
        bytes.fromhex(excess_fee_refund_address[2:]),
        bytes.fromhex(data[2:])
    ]
    encoded_data = rlp.encode(fields)
    mm = b'\x69' + encoded_data
    return Web3.keccak(hexstr=(Web3.to_hex(mm))).hex()


def calculate_deposit_tx_id(l2_chain_id, message_number, from_address, to_address, value):
    fields = [
        (l2_chain_id),
        convert_int_bytes((message_number), 32),
        bytes.fromhex(from_address[2:]),
        bytes.fromhex(to_address[2:]),
        (value)
    ]

    encoded_data = rlp.encode(fields)
    mm = b'\x64' + encoded_data
    return Web3.keccak(hexstr=(Web3.to_hex(mm))).hex()


if __name__ == "__main__":
    l2_chain_id = 42161
    from_address = "0xeA3123E9d9911199a6711321d1277285e6d4F3EC"
    message_number = 20556
    l1_base_fee = 25249467480
    dest_address = "0x6c411aD3E74De3E7Bd422b94A27770f5B86C623B"
    l2_call_value = 600000000000000000
    l1_value = 600360471887006336
    max_submission_fee = 324422087006336
    excess_fee_refund_address = "0xa2e06c19EE14255889f0Ec0cA37f6D0778D06754"
    call_value_refund_address = "0xa2e06c19EE14255889f0Ec0cA37f6D0778D06754"
    gas_limit = 120166
    max_fee_per_gas = 300000000
    data = "0x2e567b36000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a2e06c19ee14255889f0ec0ca37f6d0778d06754000000000000000000000000a2e06c19ee14255889f0ec0ca37f6d0778d067540000000000000000000000000000000000000000000000000853a0d2313c000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

    mid = "0x69f901e882a4b1a0000000000000000000000000000000000000000000000000000000000000504c94ea3123e9d9911199a6711321d1277285e6d4f3ec8505e0fc4c58880854e8ab1802ca808411e1a3008301d566946c411ad3e74de3e7bd422b94a27770f5b86c623b880853a0d2313c000094a2e06c19ee14255889f0ec0ca37f6d0778d067548701270f6740d88094a2e06c19ee14255889f0ec0ca37f6d0778d06754b901442e567b36000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000a2e06c19ee14255889f0ec0ca37f6d0778d06754000000000000000000000000a2e06c19ee14255889f0ec0ca37f6d0778d067540000000000000000000000000000000000000000000000000853a0d2313c000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

    res = calculate_submit_retryable_id(
          l2_chain_id, message_number, from_address, l1_base_fee, dest_address, l2_call_value, l1_value, max_submission_fee,
          excess_fee_refund_address, call_value_refund_address, gas_limit, max_fee_per_gas, data
        )
    print(f"get res ID  : {res}")
    assert res == "0x8ba13904639c7444d8578cc582a230b8501c9f0f7903f5069d276fdd3a7dea44"
    print("ok!")