from sqlalchemy import BIGINT, INT, JSON, NUMERIC, TIMESTAMP, BigInteger, Column, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import declarative_base

from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera_udf.bridge.arbitrum.arb_parser import (
    ArbitrumStateBatchConfirmed,
    ArbitrumStateBatchCreated,
    ArbitrumTransactionBatch,
)

Base = declarative_base()


class L1ToL2BridgeTransactions(Base):
    __tablename__ = "deposited_transactions"

    msg_hash = Column(BYTEA, primary_key=True)
    version = Column(BIGINT)
    index = Column(BIGINT)
    l1_block_number = Column(BIGINT)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    l1_from_address = Column(BYTEA)
    l1_to_address = Column(BYTEA)
    l2_block_number = Column(BIGINT)
    l2_block_timestamp = Column(TIMESTAMP)
    l2_block_hash = Column(BYTEA)
    l2_transaction_hash = Column(BYTEA)
    l2_from_address = Column(BYTEA)
    l2_to_address = Column(BYTEA)
    amount = Column(NUMERIC(100))
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    l1_token_address = Column(BYTEA)
    l2_token_address = Column(BYTEA)
    extra_info = Column(JSON)
    _type = Column(INT)
    sender = Column(BYTEA)
    target = Column(BYTEA)
    value = Column(NUMERIC(100))
    gas_limit = Column(NUMERIC(100))
    data = Column(BYTEA)


class L2ToL1BridgeTransactions(Base):
    __tablename__ = "withdrawn_transactions"

    msg_hash = Column(BYTEA, primary_key=True)
    version = Column(BIGINT)
    index = Column(BIGINT)
    l2_block_number = Column(BIGINT)
    l2_block_timestamp = Column(TIMESTAMP)
    l2_block_hash = Column(BYTEA)
    l2_transaction_hash = Column(BYTEA)
    l2_from_address = Column(BYTEA)
    l2_to_address = Column(BYTEA)
    l1_block_number = Column(BIGINT)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    l1_from_address = Column(BYTEA)
    l1_to_address = Column(BYTEA)
    amount = Column(NUMERIC(100))
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    l1_token_address = Column(BYTEA)
    l2_token_address = Column(BYTEA)
    extra_info = Column(JSON)
    _type = Column(BIGINT)
    l1_proven_transaction_hash = Column(BYTEA)
    l1_proven_block_number = Column(BIGINT)
    l1_proven_block_timestamp = Column(TIMESTAMP)
    l1_proven_block_hash = Column(BYTEA)
    l1_proven_from_address = Column(BYTEA)
    l1_proven_to_address = Column(BYTEA)


class StateBatches(Base):
    __tablename__ = "op_state_batches"

    batch_index = Column(BIGINT, primary_key=True)
    previous_total_elements = Column(BIGINT)
    batch_size = Column(INT)
    l1_block_number = Column(BIGINT)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    extra_data = Column(BYTEA)
    batch_root = Column(BYTEA)


class ArbitrumTransactionBatches(Base):
    __tablename__ = "arbitrum_transaction_batches"

    batch_index = Column(BigInteger, primary_key=True)
    l1_block_number = Column(BigInteger)
    l1_block_timestamp = Column(DateTime)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    batch_root = Column(BYTEA)
    start_block_number = Column(BigInteger)
    end_block_number = Column(BigInteger)
    transaction_count = Column(Integer)
    block_count = Column(Integer)


class ArbitrumStateBatches(Base):
    __tablename__ = "arbitrum_state_batches"

    node_num = Column(BigInteger, primary_key=True)
    create_l1_block_number = Column(BigInteger)
    create_l1_block_timestamp = Column(DateTime)
    create_l1_block_hash = Column(BYTEA)
    create_l1_transaction_hash = Column(BYTEA)

    l1_block_number = Column(BigInteger)
    l1_block_timestamp = Column(DateTime)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)

    parent_node_hash = Column(BYTEA)
    node_hash = Column(BYTEA)
    block_hash = Column(BYTEA)
    send_root = Column(BYTEA)
    start_block_number = Column(BigInteger)
    end_block_number = Column(BigInteger)
    transaction_count = Column(Integer)
    block_count = Column(Integer)


L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1 = "l1_to_l2_transactions_op_deposited_on_l1"
L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN = "l2_to_l1_transactions_op_withdrawn_proven_on_l1"
L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED = "l2_to_l1_transactions_op_withdrawn_finalized_on_l1"
OP_STATE_BATCH_TRANSACTION = "op_state_batch_transaction"
L1_TO_L2_DEPOSITED_TRANSACTION_ON_L2 = "l1_to_l2_transactions_op_deposited_on_l2"
L2_TO_L1_WITHDRAWN_TRANSACTION_ON_l2 = "l2_to_l1_transactions_op_withdrawn_on_l2"
ARB_L1ToL2_ON_L1 = "arbitrum_l1_to_l2_on_l1"
ARB_L1ToL2_ON_L2 = "arbitrum_l1_to_l2_on_l2"
ARB_L2ToL1_ON_L1 = "arbitrum_l2_to_l1_on_l1"
ARB_L2ToL1_ON_L2 = "arbitrum_l2_to_l1_on_l2"

bridge_items = {
    L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1: L1ToL2BridgeTransactions,
    L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN: L2ToL1BridgeTransactions,
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED: L2ToL1BridgeTransactions,
    OP_STATE_BATCH_TRANSACTION: StateBatches,
    L1_TO_L2_DEPOSITED_TRANSACTION_ON_L2: L1ToL2BridgeTransactions,
    L2_TO_L1_WITHDRAWN_TRANSACTION_ON_l2: L2ToL1BridgeTransactions,
    ArbitrumTransactionBatch.type(): ArbitrumTransactionBatches,
    ArbitrumStateBatchCreated.type(): ArbitrumStateBatches,
    ArbitrumStateBatchConfirmed.type(): ArbitrumStateBatches,
    ARB_L1ToL2_ON_L1: L1ToL2BridgeTransactions,
    ARB_L1ToL2_ON_L2: L1ToL2BridgeTransactions,
    ARB_L2ToL1_ON_L1: L2ToL1BridgeTransactions,
    ARB_L2ToL1_ON_L2: L2ToL1BridgeTransactions,
}


def format_bridge_data(dict):
    return {
        **dict,
        **{
            "model": bridge_items[dict["type"]],
            "update_columns": [dict.keys()],
        },
    }


def convert_bridge_column(dict):
    pg_dict = {}
    for key, value in dict.items():
        if key in ["model", "update_columns", "item"]:
            pass
        elif value is None:
            pg_dict[key] = None
        elif isinstance(value, str) and value.startswith("0x"):
            pg_dict[key] = hex_str_to_bytes(value)
        elif key.endswith("_timestamp"):
            pg_dict[key] = (func.to_timestamp(value),)
        else:
            pg_dict[key] = value
    return pg_dict


def convert_bridge_items(item_type, items, session):
    if item_type == OP_STATE_BATCH_TRANSACTION:
        # TODO: patch state batches from postgres
        pass
    for item in items:
        yield convert_bridge_column(item)
