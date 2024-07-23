from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, TIMESTAMP, NUMERIC, BOOLEAN, JSONB, VARCHAR

from common.models import db


class Tokens(db.Model):
    __tablename__ = 'tokens'

    address = Column(BYTEA, primary_key=True)
    token_type = Column(VARCHAR)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    decimals = Column(NUMERIC(100))
    total_supply = Column(NUMERIC(100))
    update_block_number = Column(BIGINT)

    holder_count = Column(INTEGER, default=0)
    transfer_count = Column(INTEGER, default=0)
    icon_url = Column(VARCHAR)
    urls = Column(JSONB)
    volume_24h = Column(NUMERIC(38, 2))
    price = Column(NUMERIC(38, 6))
    previous_price = Column(NUMERIC(38, 6))
    market_cap = Column(NUMERIC(38, 2))
    on_chain_market_cap = Column(NUMERIC(38, 2))
    is_verified = Column(BOOLEAN, default=False)

    cmc_id = Column(INTEGER)
    cmc_slug = Column(VARCHAR)
    gecko_id = Column(VARCHAR)
    description = Column(VARCHAR)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('address'),
    )




Index('tokens_symbol_index', Tokens.symbol)
Index('tokens_type_index', Tokens.token_type)
