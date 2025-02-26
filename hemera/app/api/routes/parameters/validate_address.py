#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/11 14:46
# @Author  ideal93
# @File  validate_address.py
# @Brief
from fastapi import HTTPException, Path


def is_eth_address(address: str) -> bool:
    if len(address) != 42 or address[:2] != "0x":
        return False
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


async def external_api_validate_address(
    address: str = Path(
        ...,
        description="""
Ethereum Address or ENS Name

This parameter accepts both Ethereum addresses and Ethereum Name Service (ENS) names.
An Ethereum address is a 42-character string starting with '0x', followed by 40 hexadecimal characters (0-9, a-f).
Example:
    - Ethereum address: `0x32Be343B94f860124dC4fEe278FDCBD38C102D88`

An ENS name is a human-readable name ending in '.eth', which is mapped to an Ethereum address.
ENS names are case-insensitive.
Example:
    - ENS name: `vitalik.eth`

If the provided address is invalid, a 400 HTTP exception will be raised.
        """,
    )
) -> str:
    if is_eth_address(address):  # TODO: or is_ens_name(address):
        return address
    raise HTTPException(status_code=400, detail="Invalid Address")


async def internal_api_validate_address(address: str = Path(..., description="""Ethereum Address""")) -> str:
    standardized_address = address.lower()
    if not standardized_address.startswith("0x"):
        standardized_address = "0x" + standardized_address
    if is_eth_address(standardized_address):
        return standardized_address

    raise HTTPException(status_code=400, detail="Invalid Address")
