#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/5 10:07
# @Author  will
# @File  test_multicall_helper.py
# @Brief
import pytest
from web3 import Web3

from common.utils.abi_code_utils import Function
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

DEFAULT_ETHEREUM_RPC = ""


@pytest.mark.indexer
@pytest.mark.multicall_helper
def test_mutlicall_helper():
    web3 = Web3(Web3.HTTPProvider(DEFAULT_ETHEREUM_RPC))
    multicall_helper = MultiCallHelper(web3, {"batch_size": 100, "multicall": True, "max_workers": 10})

    usdt = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    dai = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    name_function = Function(
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "name", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    )
    block_number = 2000_0000
    call1 = Call(target=usdt, function_abi=name_function, block_number=block_number)
    call2 = Call(target=usdc, function_abi=name_function, block_number=block_number)
    call3 = Call(target=dai, function_abi=name_function, block_number=block_number)
    multicall_helper.execute_calls([call1, call2, call3])
    assert (call1.returns["name"]) == "Tether USD"
    assert (call2.returns["name"]) == "USD Coin"
    assert (call3.returns["name"]) == "Dai Stablecoin"

    balance_of_function = Function(
        {
            "constant": True,
            "inputs": [{"name": "who", "type": "address"}],
            "name": "balanceOf",
            "outputs": [
                {"name": "who", "type": "uint256"},
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    )
    call = Call(
        target=usdt,
        function_abi=balance_of_function,
        parameters=["0x5041ed759Dd4aFc3a72b8192C143F72f4724081A"],
        block_number=21119829,
    )
    multicall_helper.execute_calls([call])
    assert call.returns["who"] == 301722821308228

    aave_lending_pool = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    fn = Function(
        {
            "inputs": [],
            "name": "getReservesList",
            "outputs": [{"internalType": "address[]", "name": "reserves", "type": "address[]"}],
            "stateMutability": "view",
            "type": "function",
        }
    )
    call = Call(target=aave_lending_pool, function_abi=fn, block_number=21119829)
    multicall_helper.execute_calls([call])
    assert len(call.returns["reserves"]) == 37
