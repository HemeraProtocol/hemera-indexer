from sqlalchemy import Column, Integer, String, TIMESTAMP, PrimaryKeyConstraint, func, Index
from sqlalchemy.dialects.postgresql import BOOLEAN

from common.models import HemeraModel


class ENSMiddle(HemeraModel):
    __tablename__ = "ens_middle"

    transaction_hash = Column(String, primary_key=True)
    log_index = Column(Integer, primary_key=True)
    block_number = Column(Integer)
    block_hash = Column(String)
    block_timestamp = Column(TIMESTAMP)
    method = Column(String)
    event_name = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    base_node = Column(String)  # 一级域名的NameHash 譬如 eth
    node = Column(String)  # 完整域名的NameHash
    label = Column(String)  # name的keccak-256
    name = Column(String)
    expires = Column(TIMESTAMP)  # 过期时间
    owner = Column(String)
    resolver = Column(String)  # 解析器地址
    address = Column(String)  # 该域名解析到的地址
    reverse_base_node = Column(String)
    reverse_node = Column(String)
    reverse_label = Column(String)
    reverse_name = Column(String)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('transaction_hash', 'log_index', name='ens_tnx_log_index'),
    )


Index('ens_idx_block_number_log_index', ENSMiddle.block_number, ENSMiddle.log_index.desc())
