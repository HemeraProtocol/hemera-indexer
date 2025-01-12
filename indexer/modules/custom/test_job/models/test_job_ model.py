from common.models import HemeraModel, general_converter

from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

class TestJobModel(HemeraModel):
    __tablename__ = 'test_job_table'

    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(BIGINT)
    token_address = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)
    log_index = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (
        PrimaryKeyConstraint('token_address', 'log_index'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TestJobDomain",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]

Index(
    "test_job_table_address_id_index",
    TestJobModel.token_address,
    TestJobModel.log_index,
)

