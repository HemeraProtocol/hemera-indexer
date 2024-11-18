from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, JSONB, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class ApiKey(HemeraModel):
    __tablename__ = "api_key"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    api_key = Column(VARCHAR(255), unique=True)
    limits = Column(JSONB)
    expires_at = Column(TIMESTAMP)
    description = Column(VARCHAR(255))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
