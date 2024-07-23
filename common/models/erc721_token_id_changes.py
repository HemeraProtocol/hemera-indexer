from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from common.models import HemeraModel, general_converter


class ERC721TokenIdChanges(HemeraModel):
    __tablename__ = 'erc721_token_id_changes'

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_owner = Column(BYTEA)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'token_id', 'block_number'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'ERC721TokenIdChange',
                'conflict_do_update': False,
                'update_strategy': None,
                'converter': general_converter,
            }
        ]


Index('erc721_change_address_id_number_desc_index',
      ERC721TokenIdChanges.address, ERC721TokenIdChanges.token_id, desc(ERC721TokenIdChanges.block_number))
