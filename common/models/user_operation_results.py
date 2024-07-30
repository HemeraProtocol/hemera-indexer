from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, NUMERIC, BOOLEAN, TEXT, VARCHAR

from common.models import HemeraModel, general_converter


class UserOperationResult(HemeraModel):
    __tablename__ = "user_operations_results"

    user_op_hash = Column(VARCHAR(66), primary_key=True)
    sender = Column(VARCHAR(42))
    paymaster = Column(VARCHAR(42))
    nonce = Column(INTEGER)
    status = Column(BOOLEAN)
    actual_gas_cost = Column(NUMERIC)
    actual_gas_used = Column(INTEGER)

    init_code = Column(TEXT)
    call_data = Column(TEXT)
    call_gas_limit = Column(INTEGER)
    verification_gas_limit = Column(INTEGER)
    pre_verification_gas = Column(INTEGER)
    max_fee_per_gas = Column(INTEGER)
    max_priority_fee_per_gas = Column(INTEGER)
    paymaster_and_data = Column(TEXT)
    signature = Column(TEXT)

    transactions_hash = Column(VARCHAR(66))
    transactions_index = Column(INTEGER)
    block_number = Column(INTEGER)
    block_timestamp = Column(TIMESTAMP)
    bundler = Column(VARCHAR(42))
    start_log_index = Column(INTEGER)
    end_log_index = Column(INTEGER)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'UserOperationsResult',
                'conflict_do_update': False,
                'update_strategy': None,
                'converter': general_converter,
            }
        ]


Index('transactions_hash_index', UserOperationResult.transactions_hash)
