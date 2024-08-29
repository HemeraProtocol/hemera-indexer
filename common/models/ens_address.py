from sqlalchemy import Column, String, TIMESTAMP, func

from common.models import HemeraModel, general_converter


class ENSAddress(HemeraModel):
    __tablename__ = "ens_address"

    address = Column(String, primary_key=True)
    name = Column(String)
    reverse_node = Column(String)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ENSAddressD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
