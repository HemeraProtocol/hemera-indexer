from sqlalchemy import Column, Index, desc, func, text
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.trace import Trace


class Traces(HemeraModel):
    __tablename__ = "traces"

    trace_id = Column(VARCHAR, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    input = Column(BYTEA)
    output = Column(BYTEA)
    trace_type = Column(VARCHAR)
    call_type = Column(VARCHAR)
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    subtraces = Column(INTEGER)
    trace_address = Column(ARRAY(INTEGER))
    error = Column(TEXT)
    status = Column(INTEGER)
    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    transaction_index = Column(INTEGER)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __query_order__ = [block_number, transaction_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Trace,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("traces_transaction_hash_index", Traces.transaction_hash)
Index("traces_block_number_index", desc(Traces.block_number))

Index(
    "traces_from_address_block_number_index",
    Traces.from_address,
    desc(Traces.block_number),
)

Index("traces_to_address_block_number_index", Traces.to_address, desc(Traces.block_number))
