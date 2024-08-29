from sqlalchemy import Column, INTEGER, NUMERIC, TIMESTAMP, BIGINT, func, BOOLEAN, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA

from common.models import HemeraModel, general_converter


class ENSTokenTransfers(HemeraModel):
    __tablename__ = "ens_token_transfers"

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    token_id = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ENSTokenTransferD",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]