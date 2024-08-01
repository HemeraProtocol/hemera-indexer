from common.models import db
from common.models.contracts import Contracts
from common.utils.db_utils import build_entities


def get_contract_by_address(address: str, columns='*'):
    bytes_address = bytes.fromhex(address[2:])
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
