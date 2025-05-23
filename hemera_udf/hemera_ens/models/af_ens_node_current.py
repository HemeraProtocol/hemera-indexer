from datetime import datetime, timezone
from typing import Type

from psycopg2._json import Json
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR
from sqlalchemy.sql import func

from hemera.common.models import HemeraModel, get_column_type
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.indexer.domains import Domain
from hemera_udf.hemera_ens.ens_domain import ENSAddressChangeD, ENSNameRenewD, ENSRegisterD


def ens_general_converter(table: Type[HemeraModel], data: Domain, is_update=False):
    converted_data = {}
    for key in data.__dict__.keys():
        if key in table.__table__.c:
            column_type = get_column_type(table, key)
            if isinstance(column_type, BYTEA) and not isinstance(getattr(data, key), bytes):
                if isinstance(getattr(data, key), str):
                    converted_data[key] = hex_str_to_bytes(getattr(data, key)) if getattr(data, key) else None
                elif isinstance(getattr(data, key), int):
                    converted_data[key] = getattr(data, key).to_bytes(32, byteorder="big")
                else:
                    converted_data[key] = None
            elif isinstance(column_type, TIMESTAMP):
                if isinstance(getattr(data, key), datetime):
                    converted_data[key] = getattr(data, key)
                elif isinstance(getattr(data, key), str):
                    converted_data[key] = datetime.utcfromtimestamp(
                        datetime.fromisoformat(getattr(data, key)).timestamp()
                    )
                else:
                    converted_data[key] = datetime.utcfromtimestamp(getattr(data, key)) if getattr(data, key) else None
            elif isinstance(column_type, ARRAY) and isinstance(column_type.item_type, BYTEA):
                converted_data[key] = [hex_str_to_bytes(address) for address in getattr(data, key)]
            elif isinstance(column_type, JSONB) and getattr(data, key) is not None:
                converted_data[key] = Json(getattr(data, key))
            elif isinstance(column_type, VARCHAR):
                converted_data[key] = getattr(data, key).replace("\x00", "") if getattr(data, key) else None
            else:
                converted_data[key] = getattr(data, key)

    if is_update:
        converted_data["update_time"] = datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp())

    if "reorg" in table.__table__.columns:
        converted_data["reorg"] = False

    return converted_data


class ENSRecord(HemeraModel):
    __tablename__ = "af_ens_node_current"

    node = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100))
    w_token_id = Column(NUMERIC(100))
    first_owned_by = Column(BYTEA)
    name = Column(VARCHAR)
    registration = Column(TIMESTAMP)
    expires = Column(TIMESTAMP)
    address = Column(BYTEA)
    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ENSRegisterD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_ens_node_current.block_number",
                "converter": ens_general_converter,
            },
            {
                "domain": ENSNameRenewD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_ens_node_current.block_number",
                "converter": ens_general_converter,
            },
            {
                "domain": ENSAddressChangeD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_ens_node_current.block_number",
                "converter": ens_general_converter,
            },
        ]


Index("ens_idx_address", ENSRecord.address)
# Index("ens_idx_name_md5", text("md5(name)"))
Index("ens_idx_name_md5", func.md5(ENSRecord.name), unique=False)

# because of sqlalchemy doesn't recognize 'english' with datatype REGCONFIG
# alembic could not track this index
# before sqlalchemy support this case, we suggest running this sql manually

# Index('ens_idx_name_full_text',
#       func.to_tsvector('english', (ENSRecord.name)), postgresql_using='gin')

# CREATE INDEX ens_idx_name_full_text
# ON af_ens_node_current
# USING gin (to_tsvector('english’, name::text));
