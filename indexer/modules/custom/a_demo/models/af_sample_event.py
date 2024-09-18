from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from indexer.modules.custom.hemera_ens.models.af_ens_node_current import ens_general_converter


class SampleEvent(HemeraModel):
    __tablename__ = "af_sample_event"

    transaction_hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER, nullable=False)
    log_index = Column(INTEGER, primary_key=True)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    method = Column(VARCHAR)
    event_name = Column(VARCHAR)
    topic0 = Column(VARCHAR)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)

    transfer_from = Column(BYTEA)
    transfer_to = Column(BYTEA)
    value = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index", name="sample_tnx_log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ATransferD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
