from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter

class TokenTransfer(HemeraModel):
    __tablename__ = "token_transfer"

    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    token_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("token_address", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TokenTransfer",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]

Index(
    "token_transfer_address_index",
    TokenTransfer.token_address,
    TokenTransfer.log_index,
)
