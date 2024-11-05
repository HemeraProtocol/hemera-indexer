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


@pytest.mark.indexer
@pytest.mark.multicall_helper
def test_mutlicall_helper():
    DEFAULT_ETHEREUM_RPC = "https://eth-mainnet.blastapi.io/cd2ae8f1-6328-4eee-9679-31a3979bed74"
    web3 = Web3(Web3.HTTPProvider(DEFAULT_ETHEREUM_RPC))
    multicall_helper = MultiCallHelper(web3, {"batch_size": 100, "multicall": True, "max_workers": 10})

    usdt = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
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
    call = Call(target=usdt, function_abi=name_function, block_number=21119329)
    multicall_helper.execute_calls([call])
    print(call.returns)
    assert len(call.returns) == 1
