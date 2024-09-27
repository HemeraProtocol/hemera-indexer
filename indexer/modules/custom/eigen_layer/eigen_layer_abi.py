#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:37
# @Author  will
# @File  eigen_layer_abi.py
# @Brief
import json
from typing import cast

from web3.types import ABIEvent, ABIFunction

from indexer.utils.abi import event_log_abi_to_topic, function_abi_to_4byte_selector_str

DEPOSIT_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"staker","type":"address"},{"indexed":false,"internalType":"contract IERC20","name":"token","type":"address"},{"indexed":false,"internalType":"contract IStrategy","name":"strategy","type":"address"},{"indexed":false,"internalType":"uint256","name":"shares","type":"uint256"}],"name":"Deposit","type":"event"}
"""
    ),
)
DEPOSIT_EVENT_SIG = event_log_abi_to_topic(DEPOSIT_EVENT)

WITHDRAWAL_QUEUED_EVENT = cast(
    ABIEvent,
    json.loads(
        """
    {"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"withdrawalRoot","type":"bytes32"},{"components":[{"internalType":"address","name":"staker","type":"address"},{"internalType":"address","name":"delegatedTo","type":"address"},{"internalType":"address","name":"withdrawer","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint32","name":"startBlock","type":"uint32"},{"internalType":"contract IStrategy[]","name":"strategies","type":"address[]"},{"internalType":"uint256[]","name":"shares","type":"uint256[]"}],"indexed":false,"internalType":"struct Withdrawal","name":"withdrawal","type":"tuple"}],"name":"WithdrawalQueued","type":"event"}
"""
    ),
)
WITHDRAWAL_QUEUED_EVENT_SIG = event_log_abi_to_topic(WITHDRAWAL_QUEUED_EVENT)

WITHDRAWAL_COMPLETED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"type":"event","name":"WithdrawalCompleted","inputs":[{"type":"bytes32","name":"withdrawalRoot","indexed":false}],"anonymous":false}
    """
    ),
)
WITHDRAWAL_COMPLETED_EVENT_SIG = event_log_abi_to_topic(WITHDRAWAL_COMPLETED_EVENT)


FINISH_WITHDRAWAL_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"components":[{"internalType":"address","name":"staker","type":"address"},{"internalType":"address","name":"delegatedTo","type":"address"},{"internalType":"address","name":"withdrawer","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint32","name":"startBlock","type":"uint32"},{"internalType":"address[]","name":"strategies","type":"address[]"},{"internalType":"uint256[]","name":"shares","type":"uint256[]"}],"internalType":"struct Withdrawal[]","name":"withdrawals","type":"tuple[]"},{"internalType":"address[][]","name":"tokens","type":"address[][]"},{"internalType":"uint256[]","name":"middlewareTimesIndexes","type":"uint256[]"},{"internalType":"bool[]","name":"receiveAsTokens","type":"bool[]"}],"name":"completeQueuedWithdrawals","outputs":[],"stateMutability":"nonpayable","type":"function"}"""
    ),
)
FINISH_WITHDRAWAL_FUNCTION_4SIG = function_abi_to_4byte_selector_str(FINISH_WITHDRAWAL_FUNCTION)
