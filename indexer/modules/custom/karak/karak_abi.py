#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/20 11:07
# @Author  will
# @File  karak_abi.py
# @Brief
import json
from typing import cast

from web3.types import ABIEvent

from indexer.utils.abi import event_log_abi_to_topic

DEPOSIT_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"by","type":"address"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"assets","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"}],"name":"Deposit","type":"event"}"""
    ),
)
DEPOSIT_EVENT_SIG = event_log_abi_to_topic(DEPOSIT_EVENT)

START_WITHDRAWAL_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"vault","type":"address"},{"indexed":true,"internalType":"address","name":"staker","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"address","name":"withdrawer","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"}],"name":"StartedWithdrawal","type":"event"}
"""
    ),
)
START_WITHDRAWAL_EVENT_SIG = event_log_abi_to_topic(START_WITHDRAWAL_EVENT)

FINISH_WITHDRAWAL_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"vault","type":"address"},{"indexed":true,"internalType":"address","name":"staker","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"address","name":"withdrawer","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"},{"indexed":false,"internalType":"bytes32","name":"withdrawRoot","type":"bytes32"}],"name":"FinishedWithdrawal","type":"event"}
"""
    ),
)
FINISH_WITHDRAWAL_EVENT_SIG = event_log_abi_to_topic(FINISH_WITHDRAWAL_EVENT)
