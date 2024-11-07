#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:37
# @Author  will
# @File  eigen_layer_abi.py
# @Brief

from common.utils.abi_code_utils import Event, Function

DEPOSIT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "staker", "type": "address"},
            {"indexed": False, "internalType": "contract IERC20", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "contract IStrategy", "name": "strategy", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

WITHDRAWAL_QUEUED_BATCH_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "bytes32", "name": "withdrawalRoot", "type": "bytes32"},
            {
                "components": [
                    {"internalType": "address", "name": "staker", "type": "address"},
                    {"internalType": "address", "name": "delegatedTo", "type": "address"},
                    {"internalType": "address", "name": "withdrawer", "type": "address"},
                    {"internalType": "uint256", "name": "nonce", "type": "uint256"},
                    {"internalType": "uint32", "name": "startBlock", "type": "uint32"},
                    {"internalType": "contract IStrategy[]", "name": "strategies", "type": "address[]"},
                    {"internalType": "uint256[]", "name": "shares", "type": "uint256[]"},
                ],
                "indexed": False,
                "internalType": "struct Withdrawal",
                "name": "withdrawal",
                "type": "tuple",
            },
        ],
        "name": "WithdrawalQueued",
        "type": "event",
    }
)

WITHDRAWAL_QUEUED_EVENT = Event(
    {
        "type": "event",
        "name": "WithdrawalQueued",
        "inputs": [
            {"type": "address", "name": "depositor", "indexed": False},
            {"type": "uint96", "name": "nonce", "indexed": False},
            {"type": "address", "name": "withdrawer", "indexed": False},
            {"type": "address", "name": "delegatedAddress", "indexed": False},
            {"type": "bytes32", "name": "withdrawalRoot", "indexed": False},
        ],
        "anonymous": False,
    }
)

SHARE_WITHDRAW_QUEUED = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "depositor", "type": "address"},
            {"indexed": False, "name": "nonce", "type": "uint96"},
            {"indexed": False, "name": "strategy", "type": "address"},
            {"indexed": False, "name": "shares", "type": "uint256"},
        ],
        "name": "ShareWithdrawalQueued",
        "type": "event",
    }
)

WITHDRAWAL_COMPLETED_EVENT = Event(
    {
        "type": "event",
        "name": "WithdrawalCompleted",
        "inputs": [{"type": "bytes32", "name": "withdrawalRoot", "indexed": False}],
        "anonymous": False,
    }
)

FINISH_WITHDRAWAL_FUNCTION = Function(
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "staker", "type": "address"},
                    {"internalType": "address", "name": "delegatedTo", "type": "address"},
                    {"internalType": "address", "name": "withdrawer", "type": "address"},
                    {"internalType": "uint256", "name": "nonce", "type": "uint256"},
                    {"internalType": "uint32", "name": "startBlock", "type": "uint32"},
                    {"internalType": "address[]", "name": "strategies", "type": "address[]"},
                    {"internalType": "uint256[]", "name": "shares", "type": "uint256[]"},
                ],
                "internalType": "struct Withdrawal[]",
                "name": "withdrawals",
                "type": "tuple[]",
            },
            {"internalType": "address[][]", "name": "tokens", "type": "address[][]"},
            {"internalType": "uint256[]", "name": "middlewareTimesIndexes", "type": "uint256[]"},
            {"internalType": "bool[]", "name": "receiveAsTokens", "type": "bool[]"},
        ],
        "name": "completeQueuedWithdrawals",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
