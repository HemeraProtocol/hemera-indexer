from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel
from hemera_udf.cyber_id.domains import *
from hemera_udf.hemera_ens.models.af_ens_node_current import ens_general_converter


class CyberAddress(HemeraModel):
    __tablename__ = "cyber_address"

    address = Column(BYTEA, primary_key=True)
    name = Column(VARCHAR)
    reverse_node = Column(BYTEA)
    block_number = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CyberAddressD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > cyber_address.block_number",
                "converter": ens_general_converter,
            }
        ]


class CyberIDRecord(HemeraModel):
    __tablename__ = "cyber_id_record"

    node = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100))
    label = Column(VARCHAR)
    registration = Column(TIMESTAMP)
    address = Column(BYTEA)
    block_number = Column(BIGINT)
    cost = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CyberIDRegisterD,
                "conflict_do_update": None,
                "update_strategy": None,
                "converter": ens_general_converter,
            },
            {
                "domain": CyberAddressChangedD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= cyber_id_record.block_number",
                "converter": ens_general_converter,
            },
        ]
