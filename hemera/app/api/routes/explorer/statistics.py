#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/23 11:59
# @Author  ideal93
# @File  statistics.py
# @Brief

## /v1/explorer/statistics/contract/ranks
## /v1/explorer/statistics/address/ranks
## /v1/explorer/chart-data/daily

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import Session, func, select

from hemera.app.api.deps import ReadSessionDep
from hemera.common.models.address.stats.address_index_stats import AddressIndexStats
from hemera.common.models.contracts import Contracts
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import bytes_to_hex_str

router = APIRouter(tags=["statistics"])


class ContractStatisticsType(str, Enum):
    TRANSACTIONS_RECEIVED = "transactions_received"


class AddressStatisticsType(str, Enum):
    GAS_USED = "gas_used"
    TRANSACTIONS_SENT = "transactions_sent"


class RankResponse(BaseModel):
    address: str
    transaction_count: Optional[int]
    gas_used: Optional[float]
    tag: Optional[str]
    ens_name: Optional[str]


class RankListResponse(BaseModel):
    data: List[RankResponse]


@router.get("/v1/explorer/statistics/contract/ranks", response_model=RankListResponse)
async def get_contract_ranks(
    session: ReadSessionDep, statistics: ContractStatisticsType, limit: int = Query(10, le=100)
):
    """Get contract statistics rankings.

    Args:
        session: Database session
        statistics: Type of statistics to fetch
        limit: Number of results to return (max 100)
    """
    # Get contract addresses
    contract_addresses = select(Contracts.address)
    one_day_ago = datetime.now() - timedelta(days=1)

    if statistics == ContractStatisticsType.TRANSACTIONS_RECEIVED:
        query = (
            select(
                Transactions.to_address.label("address"), func.count().label("transaction_count"), AddressIndexStats.tag
            )
            .join(AddressIndexStats, Transactions.to_address == AddressIndexStats.address, isouter=True)
            .where(Transactions.block_timestamp > one_day_ago, Transactions.to_address.in_(contract_addresses))
            .group_by(Transactions.to_address, AddressIndexStats.tag)
            .order_by(func.count().desc())
            .limit(limit)
        )

    results = session.exec(query).all()

    return {
        "data": [
            RankResponse(
                address=bytes_to_hex_str(result.address), transaction_count=result.transaction_count, tag=result.tag
            )
            for result in results
        ]
    }


@router.get("/v1/explorer/statistics/address/ranks", response_model=RankListResponse)
async def get_address_ranks(session: ReadSessionDep, statistics: AddressStatisticsType, limit: int = Query(10, le=100)):
    """Get address statistics rankings."""
    one_day_ago = datetime.now() - timedelta(days=1)

    if statistics == AddressStatisticsType.GAS_USED:
        query = (
            select(
                Transactions.from_address.label("address"),
                func.sum(Transactions.receipt_gas_used).label("gas_used"),
                AddressIndexStats.tag,
            )
            .join(AddressIndexStats, Transactions.from_address == AddressIndexStats.address, isouter=True)
            .where(Transactions.block_timestamp > one_day_ago)
            .group_by(Transactions.from_address, AddressIndexStats.tag)
            .order_by(func.sum(Transactions.receipt_gas_used).desc())
            .limit(limit)
        )
    else:  # TRANSACTIONS_SENT
        query = (
            select(
                Transactions.from_address.label("address"),
                func.count().label("transaction_count"),
                AddressIndexStats.tag,
            )
            .join(AddressIndexStats, Transactions.from_address == AddressIndexStats.address, isouter=True)
            .where(Transactions.block_timestamp > one_day_ago)
            .group_by(Transactions.from_address, AddressIndexStats.tag)
            .order_by(func.count().desc())
            .limit(limit)
        )

    results = session.exec(query).all()

    # Get ENS names for addresses
    addresses = [bytes_to_hex_str(r.address) for r in results]
    ens_mapping = get_ens_mapping(addresses)

    return {
        "data": [
            RankResponse(
                address=bytes_to_hex_str(result.address),
                transaction_count=getattr(result, "transaction_count", None),
                gas_used=getattr(result, "gas_used", None),
                tag=result.tag,
                ens_name=ens_mapping.get(bytes_to_hex_str(result.address)),
            )
            for result in results
        ]
    }
