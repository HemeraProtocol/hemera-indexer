from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from hemera.app.core.db import Database


def get_read_db() -> Generator[Session, None, None]:
    with Session(Database.get_read_engine()) as session:
        yield session


def get_write_db() -> Generator[Session, None, None]:
    with Session(Database.get_write_engine()) as session:
        yield session


def get_common_db() -> Generator[Session, None, None]:
    with Session(Database.get_common_engine()) as session:
        yield session


ReadSessionDep = Annotated[Session, Depends(get_read_db)]
WriteSessionDep = Annotated[Session, Depends(get_write_db)]
CommonSessionDep = Annotated[Session, Depends(get_common_db)]
"""
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/login/access-token"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_current_user(session: ReadSessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[]#zzsecurity.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
"""
