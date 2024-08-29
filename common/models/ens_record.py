from sqlalchemy import TIMESTAMP, Column, Index, String, UniqueConstraint, func

from common.models import HemeraModel, general_converter


class ENSRecord(HemeraModel):
    __tablename__ = "ens_record"

    node = Column(String, primary_key=True)
    token_id = Column(String)
    owner = Column(String)
    name = Column(String)  # 域名的明文
    expires = Column(TIMESTAMP)  # 过期时间
    address = Column(String)  # 该域名解析到的地址
    reverse_name = Column(String)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("node"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ENSRegisterD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ENSRegisterTokenD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ENSNameRenewD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "ENSAddressChangeD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index("ens_idx_address", ENSRecord.address)
Index("ens_idx_name", ENSRecord.name)
Index("ens_idx_reverse_name", ENSRecord.reverse_name)