from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class StoryLicenseTokenMint(FilterData):
    transaction_hash: str
    log_index: int
    caller: str
    licensor_ip_id: str
    license_template: str
    license_terms_id: int
    amount: int
    receiver: str
    start_license_token_id: int
    block_number: int
