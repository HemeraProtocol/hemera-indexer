from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.karak.domains import KarakActionD


class AfKarakRecords(HemeraModel):
    __tablename__ = "af_karak_records"
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    method = Column(VARCHAR)
    event_name = Column(VARCHAR)
    topic0 = Column(VARCHAR)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)

    token = Column(VARCHAR)
    vault = Column(BYTEA)
    amount = Column(NUMERIC(100))
    balance = Column(NUMERIC(100))
    staker = Column(VARCHAR)
    operator = Column(VARCHAR)
    withdrawer = Column(VARCHAR)
    shares = Column(NUMERIC(100))
    withdrawroot = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": KarakActionD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
