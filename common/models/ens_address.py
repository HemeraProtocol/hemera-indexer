from sqlalchemy import TIMESTAMP, Column, String, func, BIGINT

from common.models import HemeraModel, general_converter


class ENSAddress(HemeraModel):
    __tablename__ = "af_ens_address"

    address = Column(String, primary_key=True)
    name = Column(String)
    reverse_node = Column(String)
    block_number = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ENSAddressD",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > address_current_token_balances.block_number",
                "converter": general_converter,
            }
        ]
