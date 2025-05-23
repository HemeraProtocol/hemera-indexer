from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.token_price.domains import DexBlockTokenPrice, DexBlockTokenPriceCurrent


class AfDexBlockTokenPrice(HemeraModel):
    __tablename__ = "af_dex_block_token_price"

    token_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)

    token_symbol = Column(VARCHAR)
    decimals = Column(BIGINT)

    amount = Column(NUMERIC)
    amount_usd = Column(NUMERIC)

    token_price = Column(NUMERIC)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "block_number", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": DexBlockTokenPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class AfDexBlockTokenPriceCurrent(HemeraModel):
    __tablename__ = "af_dex_block_token_price_current"

    token_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)

    token_symbol = Column(VARCHAR)
    decimals = Column(BIGINT)

    amount = Column(NUMERIC)
    amount_usd = Column(NUMERIC)

    token_price = Column(NUMERIC)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": DexBlockTokenPriceCurrent,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_dex_block_token_price_current.block_number",
                "converter": general_converter,
            }
        ]
