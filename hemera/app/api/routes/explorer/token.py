#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/20 15:02
# @Author  ideal93
# @File  token.py
# @
import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlmodel import Session, and_, desc, func, nullslast, select

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.enricher import BlockchainEnricherDep
from hemera.app.api.routes.enricher.address_enricher import Address, EnricherType
from hemera.app.api.routes.helper.token import TokenInfo
from hemera.app.api.routes.helper.token_transfers import (
    TokenTransferAbbr,
    get_token_transfers,
    get_token_transfers_by_token_address,
)
from hemera.app.api.routes.parameters.validate_address import is_eth_address
from hemera.app.core.config import settings
from hemera.app.models import SortOrder
from hemera.common.enumeration.token_type import TokenType
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.common.utils.web3_utils import to_checksum_address

router = APIRouter(tags=["tokens"])


class TokenHolderInfo(BaseModel):
    token_address: str
    wallet_address: str
    balance: str


class TokenHoldersResponse(BaseModel):
    data: List[TokenHolderInfo]
    total: int


class TokenProfileResponse(BaseModel):
    token_name: str
    token_checksum_address: str
    token_address: str
    token_symbol: str
    token_logo_url: Optional[str]
    token_urls: Optional[dict]
    social_medias: Optional[dict]
    token_description: Optional[str]
    total_supply: str
    total_holders: Optional[int]
    total_transfers: Optional[int]
    token_type: str
    type: str
    # ERC20 specific fields
    token_price: Optional[float]
    token_previous_price: Optional[float]
    decimals: Optional[float]
    token_market_cap: Optional[float]
    token_on_chain_market_cap: Optional[float]
    previous_price: Optional[float]
    gecko_url: Optional[str]
    cmc_url: Optional[str]


class TokenSortField(str, Enum):
    MARKET_CAP = "market_cap"
    VOLUME_24H = "volume_24h"
    HOLDER_COUNT = "holder_count"
    PRICE = "price"
    ON_CHAIN_MARKET_CAP = "on_chain_market_cap"
    TRANSFER_COUNT = "transfer_count"


class TokenResponse(BaseModel):
    address: str
    name: str
    symbol: str
    logo: Optional[str] = None
    description: Optional[str] = None
    total_supply: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    on_chain_market_cap: Optional[float] = None
    holder_count: Optional[int] = None
    transfer_count: Optional[int] = None
    price: Optional[float] = None


class TokenListResponse(BaseModel):
    page: int
    size: int
    total: int
    data: List[TokenResponse]


class TokenTransferItem(TokenTransferAbbr):
    token_info: Optional[TokenInfo] = None
    display_value: Optional[str]
    from_addr: Optional[Address]
    to_addr: Optional[Address]


class TokenTransferResponse(BaseModel):
    total: int
    data: List[TokenTransferItem]


# API Endpoints
@router.get("/v1/explorer/tokens", response_model=TokenListResponse)
async def api_get_tokens(
    session: ReadSessionDep,
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
    type: TokenType = Query(...),
    sort: Optional[TokenSortField] = None,
    order: SortOrder = Query(SortOrder.DESC),
    is_verified: bool = Query(False),
):
    """Get list of tokens with pagination and sorting."""
    # Set default sort field
    if not sort:
        sort = TokenSortField.MARKET_CAP if type == TokenType.ERC20 else TokenSortField.HOLDER_COUNT

    # Validate sort field based on token type
    valid_sorts = (
        [
            TokenSortField.MARKET_CAP,
            TokenSortField.VOLUME_24H,
            TokenSortField.HOLDER_COUNT,
            TokenSortField.PRICE,
            TokenSortField.ON_CHAIN_MARKET_CAP,
        ]
        if type == TokenType.ERC20
        else [TokenSortField.HOLDER_COUNT, TokenSortField.TRANSFER_COUNT]
    )

    if sort not in valid_sorts:
        raise HTTPException(status_code=400, detail="Invalid sort field for token type")

    # Build query with filters
    query = select(Tokens)
    filter_conditions = [Tokens.token_type == type.value.upper()]
    if is_verified:
        filter_conditions.append(Tokens.is_verified == True)
    query = query.where(and_(*filter_conditions))

    # Apply sorting and pagination
    sort_column = getattr(Tokens, sort.value)
    query = query.order_by(nullslast(sort_column.desc() if order == SortOrder.DESC else sort_column.asc()))
    total = session.exec(select([func.count()]).select_from(query.subquery())).one()
    query = query.offset((page - 1) * size).limit(size)

    tokens = session.exec(query).all()

    # Format response based on token type
    if type == TokenType.ERC20:
        token_list = [
            TokenResponse(
                address=bytes_to_hex_str(token.address),
                name=token.name,
                symbol=token.symbol,
                logo=token.icon_url,
                description=token.description,
                total_supply=float(token.total_supply) * 10 ** (-int(token.decimals)) if token.total_supply else None,
                volume_24h=round(token.volume_24h, 2) if token.volume_24h else None,
                market_cap=round(token.market_cap, 2) if token.market_cap else None,
                on_chain_market_cap=round(token.on_chain_market_cap, 2) if token.on_chain_market_cap else None,
                holder_count=token.holder_count,
                price=round(token.price, 4) if token.price else None,
            )
            for token in tokens
        ]
    else:
        token_list = [
            TokenResponse(
                address=bytes_to_hex_str(token.address),
                name=token.name,
                symbol=token.symbol,
                total_supply=int(token.total_supply) if token.total_supply else None,
                holder_count=token.holder_count,
                transfer_count=token.transfer_count,
            )
            for token in tokens
        ]

    return {"page": page, "size": size, "total": total, "data": token_list}


@router.get("/v1/explorer/token/{address}/profile", response_model=TokenProfileResponse)
async def api_get_token_profile(session: ReadSessionDep, address: str):
    """Get detailed profile information for a token."""
    token = session.exec(select(Tokens).where(Tokens.address == hex_str_to_bytes(address.lower()))).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Base token info
    profile = {
        "token_name": token.name,
        "token_checksum_address": to_checksum_address(token.address),
        "token_address": bytes_to_hex_str(token.address),
        "token_symbol": token.symbol,
        "token_logo_url": token.icon_url,
        "token_urls": token.urls,
        "social_medias": token.urls,
        "token_description": token.description,
        "total_supply": f"{float(token.total_supply or 0):.0f}",
        "total_holders": token.holder_count,
        "total_transfers": get_token_transfer_count(token.token_type, address),
        "token_type": token.token_type,
        "type": token_type_convert(token.token_type),
    }

    # Add ERC20-specific info
    if token.token_type == "ERC20":
        profile.update(
            {
                "token_price": token.price,
                "token_previous_price": token.previous_price,
                "decimals": float(token.decimals),
                "total_supply": format_token_supply(token.total_supply, token.decimals),
                "token_market_cap": token.market_cap,
                "token_on_chain_market_cap": token.on_chain_market_cap,
                "previous_price": token.previous_price,
                "gecko_url": f"https://www.coingecko.com/en/coins/{token.gecko_id}" if token.gecko_id else None,
                "cmc_url": f"https://coinmarketcap.com/currencies/{token.cmc_slug}/" if token.cmc_slug else None,
            }
        )

    return profile


@router.get("/v1/explorer/token/{token_address}/top_holders", response_model=TokenHoldersResponse)
async def api_get_token_top_holders(
    session: ReadSessionDep, token_address: str, page: int = Query(1, gt=0), size: int = Query(settings.PAGE_SIZE, gt=0)
):
    """Get top holders for a specific token."""
    if page <= 0 or size <= 0:
        raise HTTPException(status_code=400, detail="Invalid page or size")

    token = session.exec(select(Tokens).where(Tokens.address == hex_str_to_bytes(token_address.lower()))).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Get holders with pagination
    token_address_bytes = hex_str_to_bytes(token_address.lower())
    query = (
        select(CurrentTokenBalances)
        .where(CurrentTokenBalances.token_address == token_address_bytes)
        .order_by(desc(CurrentTokenBalances.balance))
        .offset((page - 1) * size)
        .limit(size)
    )

    holders = session.exec(query).all()
    holder_list = [
        {
            "token_address": token_address.lower(),
            "wallet_address": bytes_to_hex_str(holder.address),
            "balance": format_token_balance(holder.balance, token.decimals if token.token_type == "ERC20" else 0),
        }
        for holder in holders
    ]

    total_count = session.exec(
        select([func.count()]).where(CurrentTokenBalances.token_address == token_address_bytes)
    ).one()

    return {"data": holder_list, "total": total_count}


class TokenTransfersFilterParams:
    def __init__(
        self,
        token_address: Optional[str] = Query(
            None, description="Token contract address for filtering transfers by a specific token"
        ),
        type: TokenType = Query(TokenType.ERC20, description="Token type, e.g., ERC20, ERC721, or ERC1155"),
    ):
        self.token_address = token_address
        self.type = type
        self._validate_filters()

    def _validate_filters(self):
        if self.token_address and not is_eth_address(self.token_address):
            raise HTTPException(status_code=400, detail="Invalid token address")


@router.get("/v1/explorer/token_transfers", response_model=TokenTransferResponse)
async def api_get_token_transfers(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    page: int = Query(1, gt=0),
    size: int = Query(settings.PAGE_SIZE, gt=0),
    filters: TokenTransfersFilterParams = Depends(),
):
    if filters.token_address:
        token_transfers = get_token_transfers_by_token_address(
            session, filters.token_address, token_type=filters.type.value, limit=size, offset=(page - 1) * size
        )
    else:
        token_transfers = get_token_transfers(
            session, None, token_type=filters.type.value, limit=size, offset=(page - 1) * size
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
