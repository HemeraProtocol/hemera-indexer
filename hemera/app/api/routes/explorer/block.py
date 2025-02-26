#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/23 11:56
# @Author  ideal93
# @File  block.py.py
# @Brief

from operator import and_
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.helper.block import (
    BlockAbbr,
    BlockDetails,
    _get_last_block,
    get_block_by_number_or_hash,
    get_blocks_by_range,
)
from hemera.app.api.routes.helper.token import get_token_price
from hemera.app.api.routes.parameters.validate_block import validate_block_identifier
from hemera.app.core.config import settings
from hemera.common.models.blocks import Blocks

router = APIRouter(tags=["BLOCK"])


class BlockListResponse(BaseModel):
    data: List[BlockAbbr]
    total: int
    page: int
    size: int


@router.get("/v1/explorer/blocks", response_model=BlockListResponse)
async def get_blocks(session: ReadSessionDep, page: int = Query(1, gt=0), size: int = Query(25, gt=0)):
    """Get list of blocks with pagination.

    Args:
        session: Database session
        page: Page number
        size: Page size
    """
    latest_block_number = _get_last_block(session, columns="number") or 0
    end_block = latest_block_number - (page - 1) * size
    start_block = end_block - size + 1
    blocks = get_blocks_by_range(session, max(0, start_block), end_block)

    return BlockListResponse(data=blocks, total=latest_block_number, page=page, size=size)


@router.get("/v1/explorer/block/{number_or_hash}", response_model=BlockDetails)
async def get_block_detail(
    session: ReadSessionDep, number_or_hash: Union[str, int] = Depends(validate_block_identifier)
):
    """Get detailed information about a specific block.

    Args:
        session: Database session
        number_or_hash: Block number or hash
    """
    # Get block by number or hash

    block = get_block_by_number_or_hash(session, number_or_hash)

    if not block:
        raise HTTPException(status_code=404, detail="Cannot find block with block number or block hash")

    # Get gas fee token price
    block.gas_fee_token_price = "{0:.2f}".format(
        get_token_price(session, settings.token_configuration.gas_fee_token, block.timestamp)
    )

    # Get previous block info
    earlier_block = session.exec(
        select(Blocks).where(and_(Blocks.number == max(block.number - 1, 1), Blocks.reorg == False))
    ).first()

    if earlier_block:
        block.seconds_since_last_block = block.timestamp.timestamp() - earlier_block.timestamp.timestamp()
    else:
        block.seconds_since_last_block = None

    # Check if it's the latest block
    latest_block = _get_last_block(session, columns="number") or 0

    block.is_last_block = latest_block == block.number

    return block
