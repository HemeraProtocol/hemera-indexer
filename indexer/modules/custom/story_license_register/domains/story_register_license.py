from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class StoryLicenseRegister(FilterData):
    license_terms_id: int
    license_template: str
    transferable: bool
    royalty_policy: str
    default_minting_fee: int
    expiration: int
    commercial_use: bool
    commercial_attribution: bool
    commercializer_checker: str
    commercializer_checker_data: bytes
    commercial_rev_share: int
    commercial_rev_ceiling: int
    derivatives_allowed: bool
    derivatives_attribution: bool
    derivatives_approval: bool
    derivatives_reciprocal: bool
    derivative_rev_ceiling: int
    currency: str
    uri: str
    contract_address: str
    block_number: int
    transaction_hash: str
