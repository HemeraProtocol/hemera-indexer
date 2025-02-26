from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Union

from pydantic import BaseModel
from sqlmodel import Session, select

from hemera.common.models.prices import CoinPrices, TokenHourlyPrices, TokenPrices
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


class TokenExtraInfo(BaseModel):
    logo_url: Optional[str] = None
    price: Optional[Decimal] = None
    previous_price: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    on_chain_market_cap: Optional[Decimal] = None


class TokenInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    symbol: Optional[str] = None
    type: Optional[str] = None
    decimals: Optional[int] = None
    extra_info: Optional[TokenExtraInfo] = None

    @classmethod
    def from_db_model(cls, token: Tokens) -> "TokenInfo":
        return cls(
            name=token.name,
            address=bytes_to_hex_str(token.address),
            symbol=token.symbol,
            type=token.token_type,
            decimals=token.decimals,
            extra_info=TokenExtraInfo(
                price=token.price,
                previous_price=token.previous_price,
                logo_url=token.icon_url,
                market_cap=token.market_cap,
                on_chain_market_cap=token.on_chain_market_cap,
            ),
        )


def get_token_info(session: Session, address: Union[str, bytes]) -> Optional[TokenInfo]:
    """Get token info by its address

    Args:
        session: SQLModel session
        address: Token address

    Returns:
        Optional[TokenInfo]: Token info or None
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    token = _get_token_info(session, address)
    return TokenInfo.from_db_model(token) if token else None


def _get_token_info(session: Session, address: Union[str, bytes]) -> Optional[Tokens]:
    """Get token by its address

    Args:
        session: SQLModel session
        address: Token address

    Returns:
        Optional[Tokens]: Matching token or None
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    statement = select(Tokens).where(Tokens.address == address)
    return session.exec(statement).first()


def get_token_map(session: Session, addresses: Sequence[str]) -> dict[str, TokenInfo]:
    """Get tokens by their addresses

    Args:
        session: SQLModel session
        addresses: List of token addresses

    Returns:
        List[Tokens]: List of matching tokens
    """
    address_set = set()
    for address in addresses:
        address_set.add(hex_str_to_bytes(address))
    statement = select(Tokens).where(Tokens.address.in_(address_set))
    tokens = session.exec(statement).all()
    return {bytes_to_hex_str(token.address): TokenInfo.from_db_model(token) for token in tokens}


def get_token_price(session: Session, symbol: str, date: Optional[datetime] = None) -> Decimal:
    """Get token price

    Args:
        session: SQLModel session
        symbol: Token symbol
        date: Optional date to get token price at that date, defaults to None will get the latest price

    Returns:
        Decimal: Token price
    """
    if date:
        statement = (
            select(TokenHourlyPrices)
            .where(TokenHourlyPrices.symbol == symbol, TokenHourlyPrices.timestamp <= date)
            .order_by(TokenHourlyPrices.timestamp.desc())
        )
    else:
        statement = select(TokenPrices).where(TokenPrices.symbol == symbol).order_by(TokenPrices.timestamp.desc())

    token_price = session.exec(statement).first()
    return token_price.price if token_price else Decimal(0.0)


def get_coin_prices(session: Session, dates: List[datetime]) -> List[CoinPrices]:
    """Get coin prices for specified dates

    Args:
        session: SQLModel session
        dates: List of dates to query prices for

    Returns:
        List[CoinPrices]: List of coin prices
    """
    statement = select(CoinPrices).where(CoinPrices.block_date.in_(dates))

    coin_prices = session.exec(statement).all()
    return coin_prices


def get_latest_coin_price(session: Session) -> float:
    """Get latest coin price

    Args:
        session: SQLModel session

    Returns:
        float: Latest coin price, 0.0 if no price found
    """
    statement = select(CoinPrices).order_by(CoinPrices.block_date.desc())

    result = session.exec(statement).first()
    return float(result.price) if result and result.price else 0.0


def get_tokens_by_token_address(session: Session, token_addresses: List[str]) -> List[TokenInfo]:
    """Get token info map for specified token addresses

    Args:
        session: SQLModel session
        token_addresses: List of token addresses
    Returns:
        List[TokenInfo]: List of token info
    """
    address_set = set()
    for address in token_addresses:
        if isinstance(address, str):
            address_set.add(hex_str_to_bytes(address))
        else:
            address_set.add(address)
    statement = select(Tokens).where(Tokens.address.in_(address_set))
    tokens = session.exec(statement).all()
    return [TokenInfo.from_db_model(token) for token in tokens]
