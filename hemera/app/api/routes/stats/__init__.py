#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/26 14:01
# @Author  ideal93
# @File  __init__.py.py
# @Brief
from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import desc, func

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.helper.block import get_block_count
from hemera.app.api.routes.helper.transaction import GasStats, get_gas_stats, get_latest_txn_count, get_total_txn_count
from hemera.common.models.stats.daily_boards_stats import DailyBoardsStats

router = APIRouter(tags=["STATS"])


class SmartContractMetric(BaseModel):
    contract_address: str = Field(..., description="Smart contract address")
    minute_transaction_count: int = Field(..., description="Transaction count per minute")


class MetricsResponse(BaseModel):
    transaction_count_minute: int = Field(..., description="Number of transactions in the current minute")
    transaction_count_total: int = Field(..., description="Total transaction count")
    transaction_per_second: float = Field(..., description="Transactions per second")
    block_per_second: int = Field(..., description="Blocks generated per second")
    gas_stats: GasStats = Field(..., description="Statistics related to gas usage")
    top_active_contracts: List[SmartContractMetric] = Field(
        ..., description="Top active smart contracts based on the previous day's data"
    )


@router.get("/v1/developer/stats/metrics", response_model=MetricsResponse)
async def get_address_profile(session: ReadSessionDep):
    transaction_count_minute = get_latest_txn_count(session, timedelta(minutes=1))
    transaction_count_total = get_total_txn_count(session)
    block_times = get_block_count(session, timedelta(minutes=1))
    gas_stats = get_gas_stats(session, timedelta(minutes=1))

    top_active_contracts = []
    for i in range(20):
        top_active_contracts.append(
            SmartContractMetric(contract_address=f"0x{'{:040x}'.format(i)}", minute_transaction_count=15 + i)
        )

    return MetricsResponse(
        transaction_count_minute=transaction_count_minute,
        transaction_count_total=transaction_count_total,
        transaction_per_second=transaction_count_minute / 60.0,
        block_per_second=int(block_times / 60.0),
        gas_stats=gas_stats,
        top_active_contracts=top_active_contracts,
    )


@router.get("/v1/developer/stats/all_boards", response_model=List[str])
async def get_unique_board_ids(session: ReadSessionDep):
    query = session.query(DailyBoardsStats.board_id).distinct()
    result = query.all()
    unique_board_ids = [row[0] for row in result]
    return unique_board_ids


class ECOBoardResponse(BaseModel):
    rank: int
    board_id: str
    block_date: str
    actual_date: str
    key: str
    count: int


time_ranges = {
    "1d": lambda now: now - timedelta(days=1),
    "7d": lambda now: now - timedelta(days=7),
    "30d": lambda now: now - timedelta(days=30),
    "6m": lambda now: now - timedelta(days=180),
    "YTD": lambda now: datetime(now.year, 1, 1),
    "1y": lambda now: now - timedelta(days=365),
    "all": lambda now: datetime(2020, 1, 1),
}


@router.get("/v1/developer/stats/get_board_data", response_model=List[ECOBoardResponse])
# get("time_range", "7d")
async def get_board_data(board_id: str, time_range: str, session: ReadSessionDep):
    today = date.today()
    block_date = time_ranges[time_range](today)
    query = (
        session.query(DailyBoardsStats)
        .filter(DailyBoardsStats.board_id == board_id, DailyBoardsStats.block_date == block_date)
        .order_by(desc(DailyBoardsStats.count))
    )

    result = query.all()
    if not result:
        # handle missing data
        closest_block_date = (
            session.query(DailyBoardsStats.block_date)
            .filter(DailyBoardsStats.board_id == board_id)
            .order_by(
                func.abs(func.date_part("epoch", DailyBoardsStats.block_date) - func.date_part("epoch", block_date))
            )
            .limit(1)
            .scalar()
        )
        if not closest_block_date:
            return []
        query = (
            session.query(DailyBoardsStats)
            .filter(DailyBoardsStats.board_id == board_id, DailyBoardsStats.block_date == closest_block_date)
            .order_by(desc(DailyBoardsStats.count))
        )
        result = query.all()
    data = [
        ECOBoardResponse(
            rank=index + 1,
            board_id=row.board_id,
            block_date=block_date.strftime("%Y-%m-%d"),
            actual_date=row.block_date.strftime("%Y-%m-%d"),
            key=row.key,
            count=row.count,
        )
        for (index, row) in enumerate(result)
    ]

    return data
