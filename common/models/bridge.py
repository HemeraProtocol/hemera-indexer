"""
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, BOOLEAN, BYTEA, INTEGER, JSON, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from common.utils.config import get_config

app_config = get_config()
schema = app_config.db_read_sql_alchemy_database_config.schema


class AbstractTransactions(HemeraModel):
    __abstract__ = True

    hash = Column(VARCHAR, primary_key=True)
    nonce = Column(INTEGER)
    transaction_index = Column(INTEGER)
    from_address = Column(VARCHAR)
    to_address = Column(VARCHAR)
    value = Column(NUMERIC)
    gas = Column(INTEGER)
    gas_price = Column(INTEGER)
    input = Column(VARCHAR)
    receipt_cumulative_gas_used = Column(INTEGER)
    receipt_gas_used = Column(INTEGER)
    receipt_contract_address = Column(VARCHAR)
    receipt_root = Column(VARCHAR)
    receipt_status = Column(INTEGER)
    block_timestamp = Column(TIMESTAMP)
    block_number = Column(INTEGER)
    block_hash = Column(VARCHAR)
    max_fee_per_gas = Column(INTEGER)
    max_priority_fee_per_gas = Column(INTEGER)
    transaction_type = Column(INTEGER)
    receipt_effective_gas_price = Column(INTEGER)


class AbstractTokens(HemeraModel):
    __abstract__ = True

    address = Column(VARCHAR, primary_key=True)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    total_supply = Column(NUMERIC)
    block_number = Column(INTEGER)
    block_hash = Column(VARCHAR)
    block_timestamp = Column(TIMESTAMP)
    holder_count = Column(INTEGER)
    transfer_count = Column(INTEGER)
    logo = Column(VARCHAR)
    urls = Column(JSON)
    description = Column(VARCHAR)


class L1ToL2BridgeTransactions(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "l1_to_l2_bridge_transactions"

    msg_hash = Column(BYTEA, primary_key=True)
    version = Column(INTEGER)
    index = Column(INTEGER)
    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    l1_from_address = Column(BYTEA)
    l1_to_address = Column(BYTEA)
    l2_block_number = Column(INTEGER)
    l2_block_timestamp = Column(TIMESTAMP)
    l2_block_hash = Column(BYTEA)
    l2_transaction_hash = Column(BYTEA)
    l2_from_address = Column(BYTEA)
    l2_to_address = Column(BYTEA)
    amount = Column(NUMERIC(78))
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    l1_token_address = Column(BYTEA)
    l2_token_address = Column(BYTEA)
    extra_info = Column(JSON)
    _type = Column(INTEGER)
    sender = Column(BYTEA)
    target = Column(BYTEA)
    data = Column(BYTEA)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ArbitrumL1ToL2TransactionOnL1",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ArbitrumL1ToL2TransactionOnL2",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "OpL1ToL2DepositedTransaction",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "OpL1ToL2DepositedTransactionOnL2",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class L2ToL1BridgeTransactions(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "l2_to_l1_bridge_transactions"

    msg_hash = Column(BYTEA, primary_key=True)
    version = Column(INTEGER)
    index = Column(INTEGER)
    l2_block_number = Column(INTEGER)
    l2_block_timestamp = Column(TIMESTAMP)
    l2_block_hash = Column(BYTEA)
    l2_transaction_hash = Column(BYTEA)
    l2_from_address = Column(BYTEA)
    l2_to_address = Column(BYTEA)
    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    l1_from_address = Column(BYTEA)
    l1_to_address = Column(BYTEA)
    amount = Column(NUMERIC(78))
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    l1_token_address = Column(BYTEA)
    l2_token_address = Column(BYTEA)
    extra_info = Column(JSON)
    _type = Column(INTEGER)
    l1_proven_transaction_hash = Column(BYTEA)
    l1_proven_block_number = Column(INTEGER)
    l1_proven_block_timestamp = Column(TIMESTAMP)
    l1_proven_block_hash = Column(BYTEA)
    l1_proven_from_address = Column(BYTEA)
    l1_proven_to_address = Column(BYTEA)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ArbitrumL2ToL1TransactionOnL1",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ArbitrumL2ToL1TransactionOnL2",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "OpL2ToL1WithdrawnTransactionFinalized",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "OpL2ToL1WithdrawnTransactionOnL2",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "OpL2ToL1WithdrawnTransactionProven",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class BridgeTokens(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "bridge_tokens"

    l1_token_address = Column(BYTEA, primary_key=True)
    l2_token_address = Column(BYTEA, primary_key=True)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "BridgeToken",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class StateBatches(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "l1_state_batches"

    batch_index = Column(INTEGER, primary_key=True)
    previous_total_elements = Column(INTEGER)
    batch_size = Column(INTEGER)
    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(VARCHAR)
    l1_transaction_hash = Column(VARCHAR)
    extra_data = Column(VARCHAR)
    batch_root = Column(VARCHAR)


class OpBedrockStateBatches(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "op_bedrock_state_batches"

    batch_index = Column(INTEGER, primary_key=True)
    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(VARCHAR)
    l1_transaction_hash = Column(VARCHAR)
    start_block_number = Column(INTEGER)
    end_block_number = Column(INTEGER)
    batch_root = Column(VARCHAR)
    transaction_count = Column(INTEGER)
    block_count = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "OpStateBatch",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class ArbitrumStateBatches(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "arbitrum_state_batches"

    node_num = Column(INTEGER, primary_key=True)
    create_l1_block_number = Column(INTEGER)
    create_l1_block_timestamp = Column(TIMESTAMP)
    create_l1_block_hash = Column(VARCHAR)
    create_l1_transaction_hash = Column(VARCHAR)

    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(VARCHAR)
    l1_transaction_hash = Column(VARCHAR)

    parent_node_hash = Column(VARCHAR)
    node_hash = Column(VARCHAR)
    block_hash = Column(VARCHAR)
    send_root = Column(VARCHAR)
    start_block_number = Column(INTEGER)
    end_block_number = Column(INTEGER)
    transaction_count = Column(INTEGER)
    block_count = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ArbitrumStateBatchCreated",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ArbitrumStateBatchConfirmed",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


class MantleDABatches(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "mantle_batches"

    index = Column(INTEGER, primary_key=True)
    data_store_index = Column(INTEGER)
    upgrade_data_store_id = Column(INTEGER)
    data_store_id = Column(INTEGER)
    status = Column(INTEGER)
    confirm_at = Column(TIMESTAMP)


class MantleDAStores(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "data_stores"

    id = Column(INTEGER, primary_key=True)
    store_number = Column(INTEGER)
    duration_data_store_id = Column(INTEGER)
    index = Column(INTEGER)
    data_commitment = Column(VARCHAR)
    msg_hash = Column(VARCHAR)
    init_time = Column(TIMESTAMP)
    expire_time = Column(TIMESTAMP)
    duration = Column(INTEGER)
    # num_sys = Column(INTEGER)
    # num_par = Column(INTEGER)
    # degree = Column(INTEGER)
    store_period_length = Column(INTEGER)
    fee = Column(INTEGER)
    confirmer = Column(VARCHAR)
    header = Column(VARCHAR)
    init_tx_hash = Column(VARCHAR)
    init_gas_used = Column(INTEGER)
    init_block_number = Column(INTEGER)
    confirmed = Column(BOOLEAN)
    # eth_signed = Column(NUMERIC)
    # eigen_signed = Column(NUMERIC)
    # non_signer_pub_key_hashes = Column(ARRAY(VARCHAR))
    signatory_record = Column(VARCHAR)
    confirm_tx_hash = Column(VARCHAR)
    confirm_gas_used = Column(INTEGER)
    batch_index = Column(INTEGER)
    tx_count = Column(INTEGER)
    block_count = Column(INTEGER)


class MantleDAStoreTransactionMapping(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "data_store_tx_mapping"

    data_store_id = Column(INTEGER, primary_key=True)
    index = Column(INTEGER, primary_key=True)
    block_number = Column(INTEGER)
    transaction_hash = Column(VARCHAR)


class LineaBatches(HemeraModel):
    __table_args__ = {"schema": schema}

    number = Column(INTEGER, primary_key=True)
    verify_tx_hash = Column(VARCHAR)
    verify_block_number = Column(INTEGER)
    timestamp = Column(TIMESTAMP)
    blocks = Column(ARRAY(INTEGER))
    transactions = Column(ARRAY(VARCHAR))
    last_finalized_block_number = Column(INTEGER)
    tx_count = Column(INTEGER)
    block_count = Column(INTEGER)


class ZkEvmBatches(HemeraModel):
    __table_args__ = {"schema": schema}
    __tablename__ = "zkevm_batches"
    batch_index = Column(INTEGER, primary_key=True)
    coinbase = Column(VARCHAR)
    state_root = Column(VARCHAR)
    global_exit_root = Column(VARCHAR)
    mainnet_exit_root = Column(VARCHAR)
    rollup_exit_root = Column(VARCHAR)
    local_exit_root = Column(VARCHAR)
    acc_input_hash = Column(VARCHAR)
    timestamp = Column(TIMESTAMP)
    transactions = Column(ARRAY(VARCHAR))
    blocks = Column(ARRAY(INTEGER))
    start_block_number = Column(INTEGER)
    end_block_number = Column(INTEGER)
    block_count = Column(INTEGER)
    transaction_count = Column(INTEGER)
    sequence_batch_tx_hash = Column(VARCHAR)
    sequence_batch_block_number = Column(INTEGER)
    sequence_batch_block_timestamp = Column(TIMESTAMP)
    verify_batch_tx_hash = Column(VARCHAR)
    verify_batch_block_number = Column(INTEGER)
    verify_batch_block_timestamp = Column(TIMESTAMP)
    number = Column(INTEGER)
    send_sequences_tx_hash = Column(VARCHAR)


class OpDATransactions(AbstractTransactions):
    __tablename__ = "op_da_transactions"

    receipt_blob_gas_used = Column(INTEGER)
    receipt_blob_gas_price = Column(NUMERIC)
    blob_versioned_hashes = Column(ARRAY(VARCHAR))


class ArbitrumTransactionBatches(HemeraModel):
    __tablename__ = "arbitrum_transaction_batches"

    batch_index = Column(INTEGER, primary_key=True)
    l1_block_number = Column(INTEGER)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(VARCHAR)
    l1_transaction_hash = Column(VARCHAR)
    batch_root = Column(VARCHAR)
    start_block_number = Column(INTEGER)
    end_block_number = Column(INTEGER)
    transaction_count = Column(INTEGER)
    block_count = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ArbitrumTransactionBatch",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
"""
