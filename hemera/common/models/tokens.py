from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token import MarkBalanceToken, MarkTotalSupplyToken, Token, UpdateToken


class Tokens(HemeraModel):
    __tablename__ = "tokens"

    address = Column(BYTEA, primary_key=True)
    token_type = Column(VARCHAR)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    decimals = Column(NUMERIC(100))
    total_supply = Column(NUMERIC(100))
    block_number = Column(BIGINT)

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

    no_balance_of = Column(BOOLEAN, default=False)
    fail_balance_of_count = Column(INTEGER, default=0)
    succeed_balance_of_count = Column(INTEGER, default=0)
    no_total_supply = Column(BOOLEAN, default=False)
    fail_total_supply_count = Column(BOOLEAN, default=0)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Token,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UpdateToken,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > tokens.block_number",
                "converter": general_converter,
            },
            {
                "domain": MarkTotalSupplyToken,
                "conflict_do_update": True,
                "update_strategy": None,
                # "update_strategy": "EXCLUDED.block_number >= tokens.block_number",
                "converter": general_converter,
            },
            {
                "domain": MarkBalanceToken,
                "conflict_do_update": True,
                "update_strategy": None,
                # "update_strategy": "EXCLUDED.block_number >= tokens.block_number",
                "converter": general_converter,
            },
        ]


Index("tokens_name_index", Tokens.name)
Index("tokens_symbol_index", Tokens.symbol)
Index("tokens_type_index", Tokens.token_type)
Index("tokens_type_holders_index", Tokens.token_type, desc(Tokens.holder_count))
Index(
    "tokens_type_on_chain_market_cap_index",
    Tokens.token_type,
    desc(Tokens.on_chain_market_cap),
)

# because of sqlalchemy doesn't recognize 'english' with datatype REGCONFIG
# alembic could not track this index
# before sqlalchemy support this case, we suggest running this sql manually

# Index('tokens_tsvector_symbol_name_index',
#       func.to_tsvector('english', (Tokens.symbol + ' ' + Tokens.name)), postgresql_using='gin')

# CREATE INDEX tokens_tsvector_symbol_name_index
# ON tokens
# USING gin (to_tsvector('english', (symbol || ' ' || name)));
