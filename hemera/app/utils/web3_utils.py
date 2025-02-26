#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/22 14:19
# @Author  ideal93
# @File  web3_utils.py
# @Brief

from decimal import Decimal
from typing import Optional

from web3 import Web3

from hemera.app.core.config import settings
from hemera.common.utils.abi_code_utils import decode_data

w3 = Web3(Web3.HTTPProvider(settings.rpc))


def get_balance(address) -> Decimal:
    try:
        if not w3.is_address(address):
            return Decimal(0)
        address = w3.to_checksum_address(address)
        balance = w3.eth.get_balance(address)
        return Decimal(balance)
    except Exception as e:
        return Decimal(0)


def get_code(address) -> Optional[str]:
    try:
        if not w3.is_address(address):
            return None
        address = w3.to_checksum_address(address)
        code = w3.eth.get_code(address)
        return code.hex()
    except Exception as e:
        return None


def get_gas_price():
    try:
        return w3.eth.gas_price
    except Exception as e:
        return 0


def get_storage_at(contract_address, location):
    try:
        contract_address = w3.to_checksum_address(contract_address)
        data = w3.eth.get_storage_at(contract_address, location)
        return decode_data(["address"], data)[0]
    except Exception as e:
        print(e)
        return None
