from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class StoryLicenseAttach(FilterData):
    transaction_hash: str
    log_index: int
    caller: str
    ip_id: str
    license_template: str
    license_terms_id: int
    contract_address: str
    block_number: int
