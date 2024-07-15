from common.models import db
from common.models.contracts import Contracts


def get_contract_by_addresses(addresses):
    contracts = (db.session.query(Contracts)
                 .with_entities(Contracts.address)
                 .filter(Contracts.address.in_(list(set(addresses))))
                 .all()
                 )

    return contracts
