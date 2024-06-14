from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, VARCHAR, JSONB
from exporters.jdbc.schema import Base


class ERC1155TokenIdDetails(Base):
    __tablename__ = 'erc1155_token_id_details'

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_supply = Column(NUMERIC(78))
    token_uri = Column(VARCHAR)
    token_uri_info = Column(JSONB)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('address', 'token_id'),
    )


Index('erc1155_detail_desc_address_id_index',
      desc(ERC1155TokenIdDetails.address), ERC1155TokenIdDetails.token_id)
