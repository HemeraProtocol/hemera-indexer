from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.meme_agent.domains.fourmeme import FourMemeTokenCreateD, FourMemeTokenTradeD


class FourMemeTokenCreate(HemeraModel):
    """Database model for FourMeme token creation events"""

    __tablename__ = "af_fourmeme_token_create"

    token = Column(BYTEA, primary_key=True)
    creator = Column(BYTEA)
    request_id = Column(BIGINT)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    total_supply = Column(NUMERIC(100))
    launch_time = Column(BIGINT)
    launch_fee = Column(NUMERIC(100))
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": FourMemeTokenCreateD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class FourMemeTokenTrade(HemeraModel):
    """Database model for FourMeme token trading events (buy/sell)"""

    __tablename__ = "af_fourmeme_token_trade"

    # Using token + account + block_number + trade_type as composite primary key
    token = Column(BYTEA, primary_key=True)
    account = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    trade_type = Column(VARCHAR, primary_key=True)  # 'buy' or 'sell'

    price = Column(NUMERIC(100))
    price_usd = Column(NUMERIC)
    amount = Column(NUMERIC(100))
    cost = Column(NUMERIC(100))
    fee = Column(NUMERIC(100))
    offers = Column(NUMERIC(100))
    funds = Column(NUMERIC(100))
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": FourMemeTokenTradeD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
