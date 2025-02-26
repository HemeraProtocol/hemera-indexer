#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/26 15:19
# @Author  ideal93
# @File  txn_type.py
# @Brief

from enum import Enum


class InternalTransactionType(Enum):
    SELF_CALL = 0
    SENDER = 1
    RECEIVER = 2


class AddressTransactionType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    CREATOR = 3
    BEEN_CREATED = 4


class AddressTokenTransferType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    DEPOSITOR = 3
    WITHDRAWER = 4


class AddressNftTransferType(Enum):
    SELF_CALL = 0

    SENDER = 1
    RECEIVER = 2

    BURNER = 3
    MINTER = 4
