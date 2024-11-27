from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP, VARCHAR

from common.models import HemeraModel
from custom_jobs.hemera_ens.ens_domain import ENSAddressD
from custom_jobs.hemera_ens.models.af_ens_node_current import ens_general_converter


class ENSAddress(HemeraModel):
    __tablename__ = "af_ens_address_current"

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
                "domain": ENSAddressD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_ens_address_current.block_number",
                "converter": ens_general_converter,
            }
        ]
