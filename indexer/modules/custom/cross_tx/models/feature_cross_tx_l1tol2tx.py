from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter

class L1toL2TxOnL2(HemeraModel):
    __tablename__ = "af_cross_tx_l1tol2"
    src_owner = Column(BYTEA, primary_key=True)
    dest_owner = Column(BYTEA, primary_key=True)
    transaction_hash = Column(BYTEA)

    fee = Column(NUMERIC(100))
    token_id = Column(NUMERIC(100))
    src_chain_id = Column(NUMERIC(100))
    dest_chain_id = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("src_owner", "dest_owner"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "L1toL2TxOnL2",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
