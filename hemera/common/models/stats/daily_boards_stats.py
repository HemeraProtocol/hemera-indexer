from datetime import date
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE
from sqlmodel import Field

from hemera.common.models import HemeraModel


class DailyBoardsStats(HemeraModel, table=True):
    __tablename__ = "af_eco_boards"

    board_id: str = Field(default=None, primary_key=True)
    block_date: date = Field(sa_column=Column(DATE, primary_key=True))
    key: str = Field(default=None, primary_key=True)
    count: Optional[int] = Field(default=None, sa_column=Column(BIGINT))
