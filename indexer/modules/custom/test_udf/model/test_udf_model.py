from sqlalchemy import Column, String, Integer, BigInteger, TIMESTAMP, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA
from common.models import HemeraModel

class TestUdfModel(HemeraModel):
    __tablename__ = 'test_udf_table'

    from_address = Column(String)
    to_address = Column(String)
    value = Column(BigInteger)
    token_address = Column(String)
    block_timestamp = Column(TIMESTAMP)
    block_number = Column(BigInteger)
    transaction_hash = Column(BYTEA)
    log_index = Column(Integer)

    __table_args__ = (
        PrimaryKeyConstraint('token_address', 'log_index'),
    )

