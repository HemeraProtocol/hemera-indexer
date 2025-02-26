from typing import List, Optional, Union

from pydantic import BaseModel
from sqlmodel import Session, select

from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


class TokenBalanceAbbr(BaseModel):
    address: str
    token_address: str
    token_id: Optional[int]
    balance: str

    @classmethod
    def from_db_model(cls, balance: CurrentTokenBalances) -> "TokenBalanceAbbr":
        return cls(
            address=bytes_to_hex_str(balance.address),
            token_address=bytes_to_hex_str(balance.token_address),
            token_id=balance.token_id,
            balance=str(balance.balance),
        )


def get_address_token_balances(
    session: Session,
    address: Union[str, bytes],
) -> List[TokenBalanceAbbr]:

    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    statement = select(CurrentTokenBalances).where(CurrentTokenBalances.address == address)
    balances = session.exec(statement).all()
    return [TokenBalanceAbbr.from_db_model(balance) for balance in balances]
