#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/21 下午5:50
Author  : xuzh
Project : hemera_indexer
"""
from common.utils.abi_code_utils import Event

OP_PROTOCOL_TRANSACTION_DEPOSITED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "version", "type": "uint256"},
            {"indexed": False, "internalType": "bytes", "name": "opaqueData", "type": "bytes"},
        ],
        "name": "TransactionDeposited",
        "type": "event",
    }
)

event_mapping = {"op_transaction_deposited": OP_PROTOCOL_TRANSACTION_DEPOSITED_EVENT}
