#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/10 14:58
# @Author  will
# @File  arbitrum_bridge_parser_test.py
# @Brief
import pytest
from extractor.bridge.bedrock.bedrock_bridge_parser import parse_transaction_deposited_event
from extractor.tests.json_rpc_to_dataclass import get_transaction_from_rpc


@pytest.mark.bridge
def test_bridge_l1_to_l2():

    l2Rpc = "https://arbitrum-one-rpc.publicnode.com"
    l1Rpc = "https://ethereum-rpc.publicnode.com"

    transaction = get_transaction_from_rpc(
        "https://ethereum-rpc.publicnode.com", "0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243"
    )
    deposit_transaction = parse_transaction_deposited_event(transaction, "0x9168765ee952de7c6f8fc6fad5ec209b960b7622")
    assert deposit_transaction is not None
