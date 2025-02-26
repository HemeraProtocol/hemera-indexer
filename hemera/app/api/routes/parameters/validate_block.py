#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/11 15:45
# @Author  ideal93
# @File  validate_block.py
# @Brief

from typing import Union

from fastapi import HTTPException, Path

from hemera.common.utils.web3_utils import valid_hash


async def validate_block_identifier(
    number_or_hash: str = Path(..., description="Block number or hash")
) -> Union[str, int]:
    if number_or_hash.isnumeric():
        return number_or_hash
    hash = valid_hash(number_or_hash)
    if hash:
        return hash
    raise HTTPException(status_code=400, detail="Invalid block identifier")
