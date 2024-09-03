from sqlalchemy import TIMESTAMP, Column, Index, String, UniqueConstraint, func, NUMERIC
from sqlalchemy.dialects.postgresql import BYTEA

from common.models import HemeraModel, general_converter


class ENSRecord(HemeraModel):
    __tablename__ = "af_ens_record"

    node = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100))
    w_token_id = Column(NUMERIC(100))
    first_owned_by = Column(BYTEA)
    name = Column(String)
    registration = Column(TIMESTAMP)
    expires = Column(TIMESTAMP)
    address = Column(BYTEA)

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
