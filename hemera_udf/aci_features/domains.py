from dataclasses import asdict, dataclass
from typing import Dict, Optional

from hemera.indexer.domains import Domain


@dataclass
class AllFeatureValueRecord(Domain):
    feature_id: int
    block_number: int
    address: str
    value: dict
    update_time: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AllFeatureValueRecordTraitsActiveness(AllFeatureValueRecord):
    pass


@dataclass
class AllFeatureValueRecordBlueChipHolders(AllFeatureValueRecord):
    def __init__(
        self,
        feature_id: int,
        block_number: int,
        address: str,
        value: dict,
        update_time: Optional[int] = None,
    ):
        super().__init__(feature_id, block_number, address, value, update_time)


@dataclass
class AllFeatureValueRecordUniswapV2Info(AllFeatureValueRecord):
    def __init__(
        self,
        feature_id: int,
        block_number: int,
        address: str,
        value: dict,
        update_time: Optional[int] = None,
    ):
        super().__init__(feature_id, block_number, address, value, update_time)


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