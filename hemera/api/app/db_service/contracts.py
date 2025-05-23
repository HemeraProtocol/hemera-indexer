from hemera.common.models import db
from hemera.common.models.contracts import Contracts
from hemera.common.utils.db_utils import build_entities
from hemera.common.utils.format_utils import hex_str_to_bytes


def get_contract_by_address(address: str, columns="*"):
    bytes_address = hex_str_to_bytes(address)
    entities = build_entities(Contracts, columns)

    contract = db.session.query(Contracts).with_entities(*entities).filter(Contracts.address == bytes_address).first()

    return contract


def get_contracts_by_addresses(address_list: list[bytes], columns="*"):
    entities = build_entities(Contracts, columns)
    contracts = (
        db.session.query(Contracts)
        .with_entities(*entities)
        .filter(Contracts.address.in_(list(set(address_list))))
        .all()
    )

    return contracts
