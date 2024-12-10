from sqlalchemy import Column, Index, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.deposit_to_l2.domain.token_deposit_transaction import TokenDepositTransaction


class AFTokenDepositsTransactions(HemeraModel):
    __tablename__ = "af_token_deposits__transactions"
    transaction_hash = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA)
    chain_id = Column(BIGINT)
    contract_address = Column(BYTEA)
    token_address = Column(BYTEA)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("False"))

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenDepositTransaction,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("af_deposits_transactions_wallet_address_index", AFTokenDepositsTransactions.wallet_address)
Index("af_deposits_transactions_chain_id_index", AFTokenDepositsTransactions.chain_id)
Index("af_deposits_transactions_contract_address_index", AFTokenDepositsTransactions.contract_address)
Index("af_deposits_transactions_token_address_index", AFTokenDepositsTransactions.token_address)
Index("af_deposits_transactions_block_number_index", desc(AFTokenDepositsTransactions.block_number))
