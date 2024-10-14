#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:37
# @Author  will
# @File  eigen_layer_conf.py
# @Brief
CHAIN_CONTRACT = {
    1: {
        "DEPOSIT": {
            "address": "0x858646372cc42e1a627fce94aa7a7033e7cf075a",
            "topic": "0x7cfff908a4b583f36430b25d75964c458d8ede8a99bd61be750e97ee1b2f3a96",
        },
        "START_WITHDRAW": {
            "address": "0x39053d51b77dc0d36036fc1fcc8cb819df8ef37a",
            "topic": "0x9009ab153e8014fbfb02f2217f5cde7aa7f9ad734ae85ca3ee3f4ca2fdd499f9",
        },
        "START_WITHDRAW_2": {
            "address": "0x858646372cc42e1a627fce94aa7a7033e7cf075a",
            "topic": "0x32cf9fc97155f52860a59a99879a2e89c1e53f28126a9ab6a2ff29344299e674",
            "prev_topic": "0xcf1c2370141bbd0a6d971beb0e3a2455f24d6e773ddc20ccc1c4e32f3dd9f9f7",
        },
        "FINISH_WITHDRAW": {
            "address": "0x39053d51b77dc0d36036fc1fcc8cb819df8ef37a",
            "topic": "0xc97098c2f658800b4df29001527f7324bcdffcf6e8751a699ab920a1eced5b1d",
        },
    }
}
