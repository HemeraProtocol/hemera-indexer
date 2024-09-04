from sqlalchemy import BIGINT, NUMERIC, TIMESTAMP, Column, Index, Integer, PrimaryKeyConstraint, String, func
from sqlalchemy.dialects.postgresql import BOOLEAN, BYTEA

from common.models import HemeraModel
from common.models.ens_record import ens_general_converter


class ENSMiddle(HemeraModel):
    __tablename__ = "af_ens_event"

    transaction_hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(Integer, nullable=True)
    log_index = Column(Integer, primary_key=True)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    method = Column(String)
    event_name = Column(String)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    # namehash of .eth
    base_node = Column(BYTEA)
    # namehash of full_name
    node = Column(BYTEA)
    # keccak of name
    label = Column(BYTEA)
    name = Column(String)

    expires = Column(TIMESTAMP)

    owner = Column(BYTEA)
    resolver = Column(BYTEA)
    registrant = Column(BYTEA)
    # resolved address
    address = Column(BYTEA)
    reverse_base_node = Column(BYTEA)
    reverse_node = Column(BYTEA)
    reverse_label = Column(BYTEA)
    reverse_name = Column(String)
    token_id = Column(NUMERIC(100))
    w_token_id = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index", name="ens_tnx_log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ENSMiddleD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": ens_general_converter,
            }
        ]


Index("ens_idx_block_number_log_index", ENSMiddle.block_number, ENSMiddle.log_index.desc())
