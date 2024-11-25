from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, TEXT

from common.models import HemeraModel, general_converter

class L1toL2TxOnL2s(HemeraModel):
    __tablename__ = "af_cross_tx_l1tol2s"
    token_id = Column(TEXT, primary_key=True)
    transaction_hash = Column(BYTEA, primary_key=True )
    src_owner = Column(BYTEA)
    dest_owner = Column(BYTEA)

    token_address = Column(BYTEA)

    src_chain_id = Column(BIGINT)
    dest_chain_id = Column(BIGINT)
    amount = Column(NUMERIC(100))
    fee = Column(NUMERIC(100))
    
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_id", "transaction_hash"),)

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
