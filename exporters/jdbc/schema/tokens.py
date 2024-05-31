from datetime import datetime
from sqlalchemy import Column, VARCHAR, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, TIMESTAMP, NUMERIC
from exporters.jdbc.schema import Base


class Tokens(Base):
    __tablename__ = 'tokens'

    address = Column(BYTEA, primary_key=True)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    total_supply = Column(NUMERIC(100))
    decimals = Column(NUMERIC(100))
    token_type = Column(VARCHAR)

    holder_count = Column(INTEGER)
    transfer_count = Column(INTEGER)
    icon_url = Column(VARCHAR)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint('address'),
    )
