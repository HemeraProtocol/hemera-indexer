from sqlalchemy import Column, Computed, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, JSONB, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.contract import Contract, ContractFromTransaction


class Contracts(HemeraModel):
    __tablename__ = "contracts"

    address = Column(BYTEA, primary_key=True)
    name = Column(VARCHAR)
    contract_creator = Column(BYTEA)
    creation_code = Column(BYTEA)
    deployed_code = Column(BYTEA)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    transaction_index = Column(INTEGER)
    transaction_hash = Column(BYTEA)
    transaction_from_address = Column(BYTEA)

    official_website = Column(VARCHAR)
    description = Column(VARCHAR)
    email = Column(VARCHAR)
    social_list = Column(JSONB)
    is_verified = Column(BOOLEAN, default=False)
    is_proxy = Column(BOOLEAN)
    implementation_contract = Column(BYTEA)
    verified_implementation_contract = Column(BYTEA)
    proxy_standard = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    deployed_code_hash = Column(
        VARCHAR,
        Computed("encode(digest('0x'||encode(deployed_code, 'hex'), 'sha256'), 'hex')"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Contract,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": ContractFromTransaction,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
