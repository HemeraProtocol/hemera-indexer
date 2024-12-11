from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.domain.coin_balance import CoinBalance


class CoinBalances(HemeraModel):
    __tablename__ = "address_coin_balances"

    address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CoinBalance,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "coin_balance_address_number_desc_index",
    desc(CoinBalances.address),
    desc(CoinBalances.block_number),
)
