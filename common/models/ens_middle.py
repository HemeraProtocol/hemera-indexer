from sqlalchemy import TIMESTAMP, Column, Index, Integer, PrimaryKeyConstraint, String, func
from sqlalchemy.dialects.postgresql import BOOLEAN

from common.models import HemeraModel, general_converter


class ENSMiddle(HemeraModel):
    __tablename__ = "af_ens_middle"

    transaction_hash = Column(String, primary_key=True)
    transaction_index = Column(Integer, nullable=True)
    log_index = Column(Integer, primary_key=True)

    block_number = Column(Integer)
    block_hash = Column(String)
    block_timestamp = Column(TIMESTAMP)
    method = Column(String)
    event_name = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    # namehash of .eth
    base_node = Column(String)
    # namehash of full_name
    node = Column(String)
    # keccak of name
    label = Column(String)
    name = Column(String)

    expires = Column(TIMESTAMP)

    owner = Column(String)
    resolver = Column(String)
    registrant = Column(String)
    # resolved address
    address = Column(String)
    reverse_base_node = Column(String)
    reverse_node = Column(String)
    reverse_label = Column(String)
    reverse_name = Column(String)
    token_id = Column(String)
    w_token_id = Column(String)

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
                "converter": general_converter,
            }
        ]


Index("ens_idx_block_number_log_index", ENSMiddle.block_number, ENSMiddle.log_index.desc())
