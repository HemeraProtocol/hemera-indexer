#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/20 15:01
# @Author  ideal93
# @File  address.py
# @Brief
from http.client import HTTPException
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.enricher import BlockchainEnricherDep, EnricherType
from hemera.app.api.routes.explorer.token import TokenTransferItem, TokenTransferResponse
from hemera.app.api.routes.explorer.transaction import (
    InternalTransactionItem,
    InternalTransactionResponse,
    LogResponse,
    TransactionItem,
    TransactionResponse,
)
from hemera.app.api.routes.helper.contract import ContractInfo as DBContractInfo
from hemera.app.api.routes.helper.contract import get_contract_by_address
from hemera.app.api.routes.helper.format import format_coin_value, format_dollar_value
from hemera.app.api.routes.helper.internal_transaction import (
    get_internal_transactions_by_address,
    get_internal_transactions_count_by_address,
)
from hemera.app.api.routes.helper.log import get_logs_by_address
from hemera.app.api.routes.helper.token import TokenInfo, get_latest_coin_price, get_token_info
from hemera.app.api.routes.helper.token_balances import TokenBalanceAbbr, get_address_token_balances
from hemera.app.api.routes.helper.token_transfers import get_token_transfers_by_address
from hemera.app.api.routes.helper.transaction import get_transactions_by_address, get_transactions_count_by_address
from hemera.app.api.routes.parameters.validate_address import internal_api_validate_address
from hemera.app.core.config import settings
from hemera.app.utils.web3_utils import get_balance

router = APIRouter(tags=["ADDRESS"])


class TokenHoldingItem(TokenBalanceAbbr):
    display_value: str
    token_info: TokenInfo


class TokenHoldingResponse(BaseModel):
    data: List[TokenHoldingItem]
    total: int


class ContractInfo(DBContractInfo):
    similar_verified_addresses: List[str] = []


class AddressProfileResponse(BaseModel):
    balance: Optional[str] = "0"
    native_token_price: Optional[str] = "0"
    balance_usd: Optional[str] = "0"

    contract_info: Optional[ContractInfo] = None
    token_info: Optional[TokenInfo] = None


@router.get("/v1/explorer/address/{address}/profile", response_model=AddressProfileResponse)
async def get_address_profile(session: ReadSessionDep, address: str = Depends(internal_api_validate_address)):
    """Get address profile with balance, contract and token info."""

    balance = get_balance(address)
    native_token_price = get_latest_coin_price(session)

    contract_info = get_contract_by_address(session, address)
    token_info = None
    if contract_info:
        token_info = get_token_info(session, address)

    return AddressProfileResponse(
        balance=format_coin_value(int(balance)),
        native_token_price=format_dollar_value(native_token_price),
        balance_usd=format_dollar_value((balance / 10**18) * native_token_price),
        contract_info=contract_info,
        token_info=token_info,
    )


@router.get("/v1/explorer/address/<address>/token_holdings", response_model=TokenHoldingResponse)
@router.get("/v2/explorer/address/<address>/token_holdings", response_model=TokenHoldingResponse)
async def get_address_token_holdings(
    session: ReadSessionDep, enricher: BlockchainEnricherDep, address: str = Depends(internal_api_validate_address)
):
    token_balances = get_address_token_balances(session, address)
    enriched_token_balances = enricher.enrich(
        [token_balance.dict() for token_balance in token_balances],
        {
            EnricherType.TOKEN_INFO: {"token_address": "token_info"},
            EnricherType.TOKEN_VALUE: {"balance": "display_value"},
        },
        session,
    )
    return TokenHoldingResponse(
        data=[TokenHoldingItem(**item) for item in enriched_token_balances],
        total=len(token_balances),
    )


@router.get("/v1/explorer/address/<address>/transactions", response_model=TransactionResponse)
async def get_address_transactions(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    address: str = Depends(internal_api_validate_address),
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
):
    """Get transactions list with various filters and pagination.

    Args:
        session: Database session
        page: Page number, starting from 1
        size: Items per page
    Returns:
        TransactionResponse: Paginated transaction list with metadata

    Raises:
        HTTPException: If page*size exceeds limits or invalid parameters
    """
    # Check pagination limits

    # Get all transactions with pagination

    total_records = (get_transactions_count_by_address(session, address, use_address_index=True),)
    transactions = (
        get_transactions_by_address(session, address, use_address_index=True, limit=size, offset=(page - 1) * size),
    )

    enriched_transactions = enricher.enrich(
        [transaction.dict() for transaction in transactions],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.COIN_VALUE: {"value": "display_value"},
            EnricherType.COIN_PRICE: {"transaction_fee": "transaction_fee_usd", "display_value": "value_usd"},
        },
        session,
    )

    return TransactionResponse(
        data=[TransactionItem(**tx) for tx in enriched_transactions],
        total=total_records,
        max_display=min(settings.MAX_TRANSACTION_WITH_CONDITION, total_records),
        page=page,
        size=size,
    )


@router.get("/v1/explorer/address/<address>/token_transfers", response_model=TokenTransferResponse)
async def get_address_token_transfers(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    address: str = Depends(internal_api_validate_address),
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
):
    token_transfers = get_token_transfers_by_address(
        session, address, limit=size, offset=(page - 1) * size, use_address_index=True
    )
    enriched_token_transfers = enricher.enrich(
        [token_transfer.dict() for token_transfer in token_transfers],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.TOKEN_INFO: {"token_address": "token_info"},
        },
        session,
    )

    return TokenTransferResponse(
        total=len(enriched_token_transfers), data=[TokenTransferItem(**item) for item in enriched_token_transfers]
    )


@router.get("/v1/explorer/address/<address>/internal_transactions", response_model=InternalTransactionResponse)
async def get_address_internal_transactions(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    address: str = Depends(internal_api_validate_address),
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
):
    if page * size > settings.MAX_INTERNAL_TRANSACTION:
        raise HTTPException(
            status_code=400,
            detail=f"Showing the last {settings.MAX_INTERNAL_TRANSACTION} records only",
        )
    offset = (page - 1) * size
    total_count = get_internal_transactions_count_by_address(session, address, use_address_index=True)
    transactions = get_internal_transactions_by_address(
        session, address, use_address_index=True, limit=size, offset=offset
    )

    enriched_transactions = enricher.enrich(
        [transaction.dict() for transaction in transactions],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.COIN_VALUE: {"value": "display_value"},
        },
        session,
    )
    data = [InternalTransactionItem(**tx) for tx in enriched_transactions]

    return InternalTransactionResponse(
        data=data,
        total=total_count,
        max_display=min(total_count, settings.MAX_INTERNAL_TRANSACTION),
        page=page,
        size=size,
    )


@router.get("/v1/explorer/address/<address>/logs", response_model=LogResponse)
async def get_address_logs(session: ReadSessionDep, address: str = Depends(internal_api_validate_address)):
    logs = get_logs_by_address(session, address)
    return LogResponse(total=len(logs), data=logs)
