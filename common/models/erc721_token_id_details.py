from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, VARCHAR, JSONB, BOOLEAN

from common.models import HemeraModel, general_converter


class ERC721TokenIdDetails(HemeraModel):
    __tablename__ = 'erc721_token_id_details'

    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    token_owner = Column(BYTEA)
    token_uri = Column(VARCHAR)
    token_uri_info = Column(JSONB)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('token_address', 'token_id'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'ERC721TokenIdDetail',
                'conflict_do_update': True,
                'update_strategy': "EXCLUDED.block_number > erc721_token_id_details.block_number",
                'converter': general_converter,
            }
        ]


Index('erc721_detail_owner_address_id_index',
      desc(ERC721TokenIdDetails.token_owner),
      ERC721TokenIdDetails.token_address,
      ERC721TokenIdDetails.token_id)
