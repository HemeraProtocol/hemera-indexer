#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/9 13:37
# @Author  will
# @File  extend_multicall.py
# @Brief extend Multicall, provide more flexible config
from typing import List, Optional

from multicall import Call, Multicall
from multicall.constants import w3
from multicall.utils import chain_id
from web3 import Web3

from indexer.utils.network_util import MULTICALL3_ADDRESSES, Network


class ExtendMulticall(Multicall):
    def __init__(
        self,
        calls: List[Call],
        block_id: Optional[int] = None,
        require_success: bool = True,
        gas_limit: int = 18446744073709551615,
        _w3: Web3 = w3,
    ) -> None:
        self.calls = calls
        self.block_id = block_id
        self.require_success = require_success
        self.gas_limit = gas_limit
        self.w3 = _w3
        self.chainid = chain_id(self.w3)
        self.net = Network.from_value(self.chainid)
        if require_success is True:
            multicall_map = MULTICALL3_ADDRESSES if self.net in MULTICALL3_ADDRESSES else None
            self.multicall_sig = "aggregate((address,bytes)[])(uint256,bytes[])"
        else:
            multicall_map = MULTICALL3_ADDRESSES if self.net in MULTICALL3_ADDRESSES else None
            self.multicall_sig = "tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])"
        if not multicall_map:
            raise Exception(f"No multicall map found for {self.chainid}")
        self.multicall_address = multicall_map[self.net]
