#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/10 14:58
# @Author  will
# @File  arbitrum_bridge_parser_test.py
# @Brief
import pytest

from extractor.bridge.arbitrum.arb_parser import parse_sequencer_batch_delivered
from extractor.bridge.bedrock.bedrock_bridge_parser import parse_transaction_deposited_event
from extractor.tests.json_rpc_to_dataclass import get_transaction_from_rpc
from extractor.bridge.arbitrum.arbitrum_bridge_parser import ArbitrumBridgeExtractor
from extractor.bridge.arbitrum.arb_parser import *

l2Rpc = "https://arbitrum-one-rpc.publicnode.com"
l1Rpc = "https://ethereum-rpc.publicnode.com"
contract_set = {'0x1c479675ad559dc151f6ec7ed3fbf8cee79582b6', '0x5ef0d09d1e6204141b4d37530808ed19f60fba35', '0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f', '0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a'}


@pytest.mark.bridge
def test_bridge_transaction_batch():
    l1_tnx_hash = '0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82'
    transaction = get_transaction_from_rpc(l1Rpc, l1_tnx_hash)
    res = parse_sequencer_batch_delivered(transaction, contract_set)
    print(res)


@pytest.mark.bridge
def test_bridge_state_batch():
    node_confirmed_tnx_hash = '0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d'
    node_created_tnx_hash = '0x3772f60c09379b147a80086f185b9fc3b7151a871fb48fa674e40ffa970b4aa4'
    confirm_trasnsaction = get_transaction_from_rpc(l1Rpc, node_confirmed_tnx_hash)
    create_transaction = get_transaction_from_rpc(l1Rpc, node_created_tnx_hash)
    create_res = parse_node_created(create_transaction, contract_set)
    confirm_res = parse_node_confirmed(confirm_trasnsaction, contract_set)
    print(create_res, confirm_res)


@pytest.mark.bridge
def test_bridge_l1_to_l2():
    l1_tnx_hash = '0xda4bb002306d46ac3d4ec4754f8841e72d82e876231106ecf4eb77f6244de836'
    l2_tnx_hash = '0x358bad7e9e28729b77f41ca3fdd188bcccc5004636d0cf81d7dc2abaed9c84fd'
    l1transaction = get_transaction_from_rpc(
        l1Rpc, l1_tnx_hash
    )
    l2transaction = get_transaction_from_rpc(l2Rpc, l2_tnx_hash)
    abe = ArbitrumBridgeExtractor()
    resa = abe.l1_contract_extractor([l1transaction], contract_set)
    resb = abe.l2_contract_extractor([l2transaction], contract_set)
    print(resa, resb)
