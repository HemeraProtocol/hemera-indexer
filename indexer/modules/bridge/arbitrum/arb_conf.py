#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/10 17:46
# @Author  will
# @File  arb_conf.py
# @Brief
# env = {
#     'l2_chain_id': 42161,
#     'transaction_batch_offset': 22207816
# }
env = {
    'l2_chain_id': 53457,
    'transaction_batch_offset': 0
}
NETWORK = {
    'dodo-test->arb-sepolia': {
        "l1": [],
        "l2": [],
        "batch": []
    },
    'arbitrum->eth': {
        "l1": ['0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f', '0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a', '0x0B9857ae2D4A3DBe74ffE1d7DF045bb7F96E4840'],
        "l2": ["0x000000000000000000000000000000000000006e", "0x0000000000000000000000000000000000000064",'0x5288c571Fd7aD117beA99bF60FE0846C4E84F933', '0x09e9222E96E7B4AE2a407B98d48e330053351EEe', '0x096760F208390250649E3e8763348E783AEF5562', '0x6c411aD3E74De3E7Bd422b94A27770f5B86C623B', '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'],
        "batch": ['0x5eF0D09d1E6204141B4d37530808eD19f60FBa35', '0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6']
    }
}