from dataclasses import asdict, dataclass, field
from typing import Dict, Optional

from indexer.domain import Domain, FilterData


@dataclass
class AllFeatureValueRecord(FilterData):
    feature_id: int
    block_number: int
    address: str
    value: dict
    update_time: Optional[int] = None


@dataclass
class AllFeatureValueRecordUniswapV3Pool(AllFeatureValueRecord):
    def __init__(
        self,
        feature_id: int,
        block_number: int,
        address: str,
        value: dict,
        update_time: Optional[int] = None,
    ):
        super().__init__(feature_id, block_number, address, value, update_time)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AllFeatureValueRecordUniswapV3Token(AllFeatureValueRecord):
    def __init__(
        self,
        feature_id: int,
        block_number: int,
        address: str,
        value: dict,
        update_time: Optional[int] = None,
    ):
        super().__init__(feature_id, block_number, address, value, update_time)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AllFeatureValueRecordUniswapV2TotalSupply(AllFeatureValueRecord):
    def __init__(
        self,
        feature_id: int,
        block_number: int,
        address: str,
        value: dict,
        update_time: Optional[int] = None,
    ):
        super().__init__(feature_id, block_number, address, value, update_time)

    def to_dict(self) -> Dict:
        return asdict(self)
