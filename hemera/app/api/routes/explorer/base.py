#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/19 18:31
# @Author  ideal93
# @File  base.py
# @Brief

from datetime import datetime, time, timedelta
from operator import or_
from typing import List

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.helper.block import _get_last_block
from hemera.app.api.routes.helper.format import format_dollar_value
from hemera.app.api.routes.helper.stats import get_daily_transactions_cnt
from hemera.app.api.routes.helper.token import get_token_price
from hemera.app.api.routes.helper.transaction import get_total_txn_count, get_tps_latest_10min
from hemera.app.core.config import settings
from hemera.app.core.db import Database
from hemera.app.models import (
    AddressSearchResult,
    BlockSearchResult,
    ExplorerStats,
    HealthCheckResponse,
    SearchResult,
    TokenSearchResult,
    TransactionsDayResponse,
    TransactionSearchResult,
)
from hemera.app.utils.web3_utils import get_gas_price
from hemera.common.models.blocks import Blocks
from hemera.common.models.contracts import Contracts
from hemera.common.models.tokens import Tokens
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.common.utils.web3_utils import is_eth_address, is_eth_transaction_hash

router = APIRouter(tags=["BASE"])


def get_engines_status():
    _to_status = lambda pool_status: {
        "checked_in": pool_status.checked_in(),
        "checked_out": pool_status.checked_out(),
        "overflow": pool_status.overflow(),
        "connections": pool_status.size(),
    }

    return {
        "engine_pool_status": Database.get_read_engine().pool.status(),
        "read_pool_status": Database.get_read_engine().pool.status(),
        "write_pool_status": Database.get_write_engine().pool.status(),
        "common_pool_status": Database.get_common_engine().pool.status(),
    }


@router.get("/v1/explorer/health", response_model=HealthCheckResponse)
async def health_check(session: ReadSessionDep):
    block = _get_last_block(session=session, columns=["number", "timestamp"])
    if not block:
        raise HTTPException(status_code=404, detail="No blocks found")

    return {
        "latest_block_number": block.number,
        "latest_block_timestamp": block.timestamp.isoformat(),
        **get_engines_status(),
        "status": "OK",
    }


@router.get("/v1/explorer/stats", response_model=ExplorerStats)
async def get_stats(session: ReadSessionDep):
    transaction_count = get_total_txn_count(session)

    latest_block = _get_last_block(session)

    if not latest_block:
        raise HTTPException(status_code=404, detail="No blocks found")

    latest_block_number = latest_block.number

    earlier_block_number = max(latest_block_number - 5000, 1)
    earlier_block = session.exec(select(Blocks).where(Blocks.number == earlier_block_number)).first()

    if not earlier_block:
        earlier_block = latest_block

    avg_block_time = (latest_block.timestamp.timestamp() - earlier_block.timestamp.timestamp()) / (
        (latest_block_number - earlier_block_number) or 1
    )

    transaction_tps = get_tps_latest_10min(session, latest_block.timestamp)

    latest_batch_number = 0

    btc_price = get_token_price(session, "WBTC")
    eth_price = get_token_price(session, "ETH")
    eth_price_previous = get_token_price(session, "ETH", datetime.combine(datetime.now() - timedelta(days=1), time.min))

    if settings.token_configuration.native_token == "ETH":
        native_token_price = eth_price
        native_token_price_previous = eth_price_previous
    else:
        native_token_price = get_token_price(session, settings.token_configuration.native_token)
        native_token_price_previous = get_token_price(
            session,
            settings.token_configuration.native_token,
            datetime.combine(datetime.now() - timedelta(days=1), time.min),
        )

    if settings.token_configuration.dashboard_token == settings.token_configuration.native_token:
        dashboard_token_price = native_token_price
        dashboard_token_price_previous = native_token_price_previous
    else:
        dashboard_token_price = get_token_price(session, settings.token_configuration.dashboard_token)
        dashboard_token_price_previous = get_token_price(
            session,
            settings.token_configuration.dashboard_token,
            datetime.combine(datetime.now() - timedelta(days=1), time.min),
        )

    return ExplorerStats(
        total_transactions=transaction_count,
        transaction_tps=round(transaction_tps, 2),
        latest_batch=latest_batch_number,
        latest_block=latest_block_number,
        avg_block_time=avg_block_time,
        eth_price=format_dollar_value(eth_price),
        eth_price_btc=f"{eth_price / (btc_price or 1):.5f}",
        eth_price_diff=f"{(eth_price - eth_price_previous) / (eth_price_previous or 1):.4f}",
        native_token_price=format_dollar_value(native_token_price),
        native_token_price_eth=f"{native_token_price / (eth_price or 1):.5f}",
        native_token_price_diff=(
            f"{(native_token_price - native_token_price_previous) / (native_token_price_previous or 1):.4f}"
            if native_token_price_previous != 0
            else "0"
        ),
        dashboard_token_price_eth=f"{dashboard_token_price / (eth_price or 1):.5f}",
        dashboard_token_price=format_dollar_value(dashboard_token_price),
        dashboard_token_price_diff=(
            f"{(dashboard_token_price - dashboard_token_price_previous) / (dashboard_token_price_previous or 1):.4f}"
            if dashboard_token_price_previous != 0
            else "0"
        ),
        gas_fee=f"{get_gas_price() / 10 ** 9:.1f}".rstrip("0").rstrip(".") + " Gwei",
    )


@router.get("/v1/explorer/charts/transactions_per_day", response_model=TransactionsDayResponse)
async def get_transactions_per_day(session: ReadSessionDep):
    results = get_daily_transactions_cnt(session, columns=[("block_date", "date"), "cnt"], limit=14)

    date_list = [{"value": item.date.isoformat(), "count": item.cnt} for item in results]

    return {"title": "Daily Transactions Chart", "data": date_list}


@router.get("/v1/explorer/search", response_model=List[SearchResult])
async def explorer_search(
    session: ReadSessionDep, q: str = Query(..., min_length=1, description="Search query")
) -> List[SearchResult]:
    """Search for blocks, addresses, transactions and tokens."""
    query_string = q.lower()
    search_result = []

    # Block number search
    if query_string.isdigit():
        block = session.exec(select(Blocks.hash, Blocks.number).where(Blocks.number == int(query_string))).first()
        if block:
            return [BlockSearchResult(block_hash=bytes_to_hex_str(block.hash), block_number=block.number)]

    # Wallet/contract address search
    if is_eth_address(query_string):
        # Check contract first
        contract_address = session.exec(
            select(Contracts.address).where(Contracts.address == hex_str_to_bytes(query_string))
        ).first()
        if contract_address:
            return [AddressSearchResult(wallet_address=bytes_to_hex_str(contract_address))]

        # Check from/to addresses
        for query in [
            select(Transactions.from_address.label("address")).where(Transactions.from_address == query_string),
            select(Transactions.to_address.label("address")).where(Transactions.to_address == query_string),
        ]:
            wallet = session.exec(query).first()
            if wallet:
                return [AddressSearchResult(wallet_address=bytes_to_hex_str(wallet.address))]

    # Transaction/block hash search
    if is_eth_transaction_hash(query_string):
        # Check transaction
        transaction = session.exec(
            select(Transactions.hash).where(Transactions.hash == hex_str_to_bytes(query_string))
        ).first()
        if transaction:
            return [TransactionSearchResult(transaction_hash=bytes_to_hex_str(transaction.hash))]

        # Check block
        block = session.exec(
            select(Blocks.hash, Blocks.number).where(Blocks.hash == hex_str_to_bytes(query_string))
        ).first()
        if block:
            return [BlockSearchResult(block_hash=bytes_to_hex_str(block.hash), block_number=block.number)]

    # Token search
    if len(query_string) > 1:
        tokens = session.exec(
            select(Tokens.name, Tokens.symbol, Tokens.address, Tokens.icon_url)
            .where(or_(Tokens.name.ilike(f"%{query_string}%"), Tokens.symbol.ilike(f"%{query_string}%")))
            .limit(5)
        ).all()

        search_result.extend(
            [
                TokenSearchResult(
                    token_name=token.name,
                    token_symbol=token.symbol,
                    token_address=bytes_to_hex_str(token.address),
                    token_logo_url=token.icon_url,
                )
                for token in tokens
            ]
        )

    return search_result
