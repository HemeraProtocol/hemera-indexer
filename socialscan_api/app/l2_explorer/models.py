# from sqlalchemy import ARRAY, JSON, BigInteger, Boolean, Column, DateTime, Integer, LargeBinary, Numeric, String
#
# from common.utils.config import get_config
# from common.models import db as postgres_db
# from common.models import AbstractTransactions
#
# app_config = get_config()
# schema = app_config.db_read_sql_alchemy_database_config.schema
#
#
# class L1ToL2Transactions(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "l1_to_l2_txns"
#
#     index = Column(BigInteger, primary_key=True)
#     l1_from_address = Column(String)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#     l1_token_address = Column(String)
#     l2_block_number = Column(BigInteger)
#     l2_block_timestamp = Column(DateTime)
#     l2_block_hash = Column(String)
#     l2_transaction_hash = Column(String)
#     l2_token_address = Column(String)
#     from_address = Column(String)
#     to_address = Column(String)
#     amount = Column(Numeric)
#     _type = Column(Integer)
#
#
# class L2ToL1Transactions(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "l2_to_l1_txns"
#
#     index = Column(BigInteger, primary_key=True)
#     l2_from_address = Column(String)
#     l2_block_number = Column(BigInteger)
#     l2_block_timestamp = Column(DateTime)
#     l2_block_hash = Column(String)
#     l2_transaction_hash = Column(String)
#     l2_token_address = Column(String)
#     l1_from_address = Column(String)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#     l1_token_address = Column(String)
#     from_address = Column(String)
#     to_address = Column(String)
#     amount = Column(Numeric)
#
#     l1_proven_block_number = Column(BigInteger)
#     l1_proven_block_timestamp = Column(DateTime)
#     l1_proven_txn_hash = Column(String)
#
#     l1_finalized_block_number = Column(BigInteger)
#     l1_finalized_block_timestamp = Column(DateTime)
#     l1_finalized_txn_hash = Column(String)
#
#
# class BridgeTokens(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "bridge_tokens"
#
#     l1_token_address = Column(LargeBinary, primary_key=True)
#     l2_token_address = Column(LargeBinary, primary_key=True)
#
#
# class L1ToL2BridgeTransactions(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "l1_to_l2_bridge_transactions"
#
#     msg_hash = Column(LargeBinary, primary_key=True)
#     version = Column(BigInteger)
#     index = Column(BigInteger)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(LargeBinary)
#     l1_transaction_hash = Column(LargeBinary)
#     l1_from_address = Column(LargeBinary)
#     l1_to_address = Column(LargeBinary)
#     l2_block_number = Column(BigInteger)
#     l2_block_timestamp = Column(DateTime)
#     l2_block_hash = Column(LargeBinary)
#     l2_transaction_hash = Column(LargeBinary)
#     l2_from_address = Column(LargeBinary)
#     l2_to_address = Column(LargeBinary)
#     amount = Column(Numeric(78))
#     from_address = Column(LargeBinary)
#     to_address = Column(LargeBinary)
#     l1_token_address = Column(LargeBinary)
#     l2_token_address = Column(LargeBinary)
#     extra_info = Column(JSON)
#     _type = Column(BigInteger)
#
#
# class L2ToL1BridgeTransactions(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "l2_to_l1_bridge_transactions"
#
#     msg_hash = Column(LargeBinary, primary_key=True)
#     version = Column(BigInteger)
#     index = Column(BigInteger)
#     l2_block_number = Column(BigInteger)
#     l2_block_timestamp = Column(DateTime)
#     l2_block_hash = Column(LargeBinary)
#     l2_transaction_hash = Column(LargeBinary)
#     l2_from_address = Column(LargeBinary)
#     l2_to_address = Column(LargeBinary)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(LargeBinary)
#     l1_transaction_hash = Column(LargeBinary)
#     l1_from_address = Column(LargeBinary)
#     l1_to_address = Column(LargeBinary)
#     amount = Column(Numeric(78))
#     from_address = Column(LargeBinary)
#     to_address = Column(LargeBinary)
#     l1_token_address = Column(LargeBinary)
#     l2_token_address = Column(LargeBinary)
#     extra_info = Column(JSON)
#     _type = Column(BigInteger)
#     l1_proven_transaction_hash = Column(LargeBinary)
#     l1_proven_block_number = Column(BigInteger)
#     l1_proven_block_timestamp = Column(DateTime)
#     l1_proven_block_hash = Column(LargeBinary)
#     l1_proven_from_address = Column(LargeBinary)
#     l1_proven_to_address = Column(LargeBinary)
#
#
# class StateBatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "l1_state_batches"
#
#     batch_index = Column(BigInteger, primary_key=True)
#     previous_total_elements = Column(BigInteger)
#     batch_size = Column(Integer)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#     extra_data = Column(String)
#     batch_root = Column(String)
#
#
# class OpBedrockStateBatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "op_bedrock_state_batches"
#
#     batch_index = Column(BigInteger, primary_key=True)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#     start_block_number = Column(BigInteger)
#     end_block_number = Column(BigInteger)
#     batch_root = Column(String)
#     transaction_count = Column(Integer)
#     block_count = Column(Integer)
#
#
# class ArbitrumStateBatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "arbitrum_state_batches"
#
#     node_num = Column(BigInteger, primary_key=True)
#     create_l1_block_number = Column(BigInteger)
#     create_l1_block_timestamp = Column(DateTime)
#     create_l1_block_hash = Column(String)
#     create_l1_transaction_hash = Column(String)
#
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#
#     parent_node_hash = Column(String)
#     node_hash = Column(String)
#     block_hash = Column(String)
#     send_root = Column(String)
#     start_block_number = Column(BigInteger)
#     end_block_number = Column(BigInteger)
#     transaction_count = Column(Integer)
#     block_count = Column(Integer)
#
#
# class MantleDABatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "mantle_batches"
#
#     index = Column(BigInteger, primary_key=True)
#     data_store_index = Column(Integer)
#     upgrade_data_store_id = Column(BigInteger)
#     data_store_id = Column(BigInteger)
#     status = Column(Integer)
#     confirm_at = Column(DateTime)
#
#
# class MantleDAStores(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "data_stores"
#
#     id = Column(BigInteger, primary_key=True)
#     store_number = Column(BigInteger)
#     duration_data_store_id = Column(BigInteger)
#     index = Column(Integer)
#     data_commitment = Column(String)
#     msg_hash = Column(String)
#     init_time = Column(DateTime)
#     expire_time = Column(DateTime)
#     duration = Column(Integer)
#     # num_sys = Column(Integer)
#     # num_par = Column(Integer)
#     # degree = Column(BigInteger)
#     store_period_length = Column(BigInteger)
#     fee = Column(BigInteger)
#     confirmer = Column(String)
#     header = Column(String)
#     init_tx_hash = Column(String)
#     init_gas_used = Column(BigInteger)
#     init_block_number = Column(BigInteger)
#     confirmed = Column(Boolean)
#     # eth_signed = Column(Numeric)
#     # eigen_signed = Column(Numeric)
#     # non_signer_pub_key_hashes = Column(ARRAY(String))
#     signatory_record = Column(String)
#     confirm_tx_hash = Column(String)
#     confirm_gas_used = Column(BigInteger)
#     batch_index = Column(BigInteger)
#     tx_count = Column(Integer)
#     block_count = Column(Integer)
#
#
# class MantleDAStoreTransactionMapping(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "data_store_tx_mapping"
#
#     data_store_id = Column(BigInteger, primary_key=True)
#     index = Column(Integer, primary_key=True)
#     block_number = Column(BigInteger)
#     transaction_hash = Column(String)
#
#
# class LineaBatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#
#     number = Column(BigInteger, primary_key=True)
#     verify_tx_hash = Column(String)
#     verify_block_number = Column(BigInteger)
#     timestamp = Column(DateTime)
#     blocks = Column(ARRAY(BigInteger))
#     transactions = Column(ARRAY(String))
#     last_finalized_block_number = Column(BigInteger)
#     tx_count = Column(Integer)
#     block_count = Column(Integer)
#
#
# class ZkEvmBatches(postgres_db.Model):
#     __table_args__ = {"schema": schema}
#     __tablename__ = "zkevm_batches"
#     batch_index = Column(BigInteger, primary_key=True)
#     coinbase = Column(String)
#     state_root = Column(String)
#     global_exit_root = Column(String)
#     mainnet_exit_root = Column(String)
#     rollup_exit_root = Column(String)
#     local_exit_root = Column(String)
#     acc_input_hash = Column(String)
#     timestamp = Column(DateTime)
#     transactions = Column(ARRAY(String))
#     blocks = Column(ARRAY(BigInteger))
#     start_block_number = Column(BigInteger)
#     end_block_number = Column(BigInteger)
#     block_count = Column(Integer)
#     transaction_count = Column(Integer)
#     sequence_batch_tx_hash = Column(String)
#     sequence_batch_block_number = Column(BigInteger)
#     sequence_batch_block_timestamp = Column(DateTime)
#     verify_batch_tx_hash = Column(String)
#     verify_batch_block_number = Column(BigInteger)
#     verify_batch_block_timestamp = Column(DateTime)
#     number = Column(BigInteger)
#     send_sequences_tx_hash = Column(String)
#
#
# class OpDATransactions(AbstractTransactions):
#     __tablename__ = "op_da_transactions"
#
#     receipt_blob_gas_used = Column(BigInteger)
#     receipt_blob_gas_price = Column(Numeric)
#     blob_versioned_hashes = Column(ARRAY(String))
#
#
# class ArbitrumTransactionBatches(postgres_db.Model):
#     __tablename__ = "arbitrum_transaction_batches"
#
#     batch_index = Column(BigInteger, primary_key=True)
#     l1_block_number = Column(BigInteger)
#     l1_block_timestamp = Column(DateTime)
#     l1_block_hash = Column(String)
#     l1_transaction_hash = Column(String)
#     batch_root = Column(String)
#     start_block_number = Column(BigInteger)
#     end_block_number = Column(BigInteger)
#     transaction_count = Column(Integer)
#     block_count = Column(Integer)
