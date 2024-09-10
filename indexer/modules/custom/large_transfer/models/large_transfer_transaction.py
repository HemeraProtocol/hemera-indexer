from sqlalchemy import Column, Computed, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class LargeTransferTransactions(HemeraModel):
    __tablename__ = "af_large_transfer_transactions"

    transaction_hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    transaction_type = Column(INTEGER)
    input = Column(BYTEA)
    # method_id = Column(VARCHAR, Computed("substring((input)::varchar for 8)::bigint::varchar"))
    nonce = Column(INTEGER)

    block_hash = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    gas = Column(NUMERIC(100))
    gas_price = Column(NUMERIC(100))
    max_fee_per_gas = Column(NUMERIC(100))
    max_priority_fee_per_gas = Column(NUMERIC(100))

    exist_error = Column(BOOLEAN)
    error = Column(TEXT)
    revert_reason = Column(TEXT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "LargeTransferTransactionD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
