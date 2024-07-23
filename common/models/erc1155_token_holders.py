from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from common.models import HemeraModel, general_converter


class ERC1155TokenHolders(HemeraModel):
    __tablename__ = 'erc1155_token_holders'

    token_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    balance_of = Column(NUMERIC(100))
    latest_call_contract_time = Column(TIMESTAMP)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('token_address', 'wallet_address', 'token_id'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'ERC1155TokenHolder',
                'conflict_do_update': True,
                'update_strategy': "EXCLUDED.block_number > erc1155_token_holders.block_number",
                'converter': general_converter,
            }
        ]


Index('erc1155_token_holders_wallet_address_index', ERC1155TokenHolders.wallet_address)
Index('erc1155_token_holders_token_address_balance_of_index',
      ERC1155TokenHolders.token_address, desc(ERC1155TokenHolders.balance_of))
