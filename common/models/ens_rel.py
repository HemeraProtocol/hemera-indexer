from sqlalchemy import Column, Integer, String, TIMESTAMP, func, UniqueConstraint, Index

from common.models import HemeraModel


class ENSRel(HemeraModel):
    __tablename__ = "ens_rel"

    id = Column(Integer, primary_key=True)
    token_id = Column(String)
    node = Column(String, unique=True)  # 完整域名的nameHash
    owner = Column(String)
    name = Column(String)  # 域名的明文
    expires = Column(TIMESTAMP)  # 过期时间
    address = Column(String)  # 该域名解析到的地址
    reverse_name = Column(String)

    inserted_at = Column(TIMESTAMP, server_default=func.now())  # 插入时间
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())  # 更新时间

    __table_args__ = (
        UniqueConstraint('node'),
    )


Index('ens_idx_address', ENSRel.address)
Index('ens_idx_name', ENSRel.name)
Index('ens_idx_reverse_name', ENSRel.reverse_name)
