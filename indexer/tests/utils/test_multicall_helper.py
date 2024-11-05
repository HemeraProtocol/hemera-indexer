#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/5 10:07
# @Author  will
# @File  test_multicall_helper.py
# @Brief
import pytest
from web3 import Web3

from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper


@pytest.mark.indexer
@pytest.mark.indexer_utils
@pytest.mark.indexer_utils.multicall_helper
def test_mutlicall_helper():
    DEFAULT_ETHEREUM_RPC = "https://ethereum-rpc.publicnode.com"
    web3 = Web3(Web3.HTTPProvider(DEFAULT_ETHEREUM_RPC))
    multicall_helper = MultiCallHelper(web3, {"batch_size": 100, "multicall": True, "max_workers": 10})
