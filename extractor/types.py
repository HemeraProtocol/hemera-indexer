from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from hexbytes import HexBytes


@dataclass
class Base(object):
    @property
    def type(self):
        raise NotImplementedError


@dataclass
class Log(Base):
    log_index: int
    address: str
    data: str
    transaction_hash: str
    transaction_index: int
    block_timestamp: int
    block_number: int
    block_hash: str
    topic0: Optional[str] = None
    topic1: Optional[str] = None
    topic2: Optional[str] = None
    topic3: Optional[str] = None

    @property
    def type(self):
        return "log"

    def get_bytes_topics(self) -> HexBytes:
        topics = ""
        for i in range(4):
            topic = getattr(self, f"topic{i}")
            if topic and i != 0:
                if topic.startswith("0x"):
                    topic = topic[2:]
                topics += topic
        return HexBytes(bytearray.fromhex(topics))

    def get_bytes_data(self) -> HexBytes:
        data = self.data
        if data.startswith("0x"):
            data = self.data[2:]
        return HexBytes(bytearray.fromhex(data))


@dataclass
class Receipt:
    transaction_hash: str
    transaction_index: int
    contract_address: str
    status: int
    logs: List[Log] = field(default_factory=list)
    root: str = Optional[None]
    cumulative_gas_used: Optional[int] = None
    gas_used: Optional[int] = None
    effective_gas_price: Optional[int] = None
    l1_fee: Optional[int] = None
    l1_fee_scalar: Optional[float] = None
    l1_gas_used: Optional[int] = None
    l1_gas_price: Optional[int] = None
    blob_gas_used: Optional[int] = None
    blob_gas_price: Optional[int] = None

    @property
    def type(self):
        return "receipt"


@dataclass
class Transaction:
    hash: str
    nonce: int
    transaction_index: int
    from_address: str
    to_address: Optional[str]
    value: int
    gas_price: int
    gas: int
    transaction_type: int
    input: str
    block_number: int
    block_timestamp: int
    block_hash: str
    # blob_versioned_hashes: List[str] = field(default_factory=list)
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    receipt: Receipt = None

    @property
    def type(self):
        return "transaction"


def dict_to_dataclass(data: Dict[str, Any], cls):
    """
    Converts a dictionary to a dataclass instance, handling nested structures.

    Args:
        data (Dict[str, Any]): The input dictionary.
        cls: The dataclass type to convert to.

    Returns:
        An instance of the specified dataclass.
    """
    fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    init_values = {}
    for field, field_type in fieldtypes.items():
        if field in data:
            origin = get_origin(field_type)
            args = get_args(field_type)
            if origin is list:
                # Handle lists
                item_type = args[0]
                init_values[field] = [
                    dict_to_dataclass(item, item_type) if isinstance(item, dict) else item for item in data[field]
                ]
            elif hasattr(field_type, "__dataclass_fields__"):
                # Handle nested dataclass
                init_values[field] = dict_to_dataclass(data[field], field_type)
            else:
                init_values[field] = data[field]
        else:
            if get_origin(field_type) is Union and type(None) in get_args(field_type):
                init_values[field] = None
            else:
                init_values[field] = field_type()
    return cls(**init_values)


def dataclass_to_dict(instance: Base) -> Dict[str, Any]:
    if not is_dataclass(instance):
        raise ValueError("dataclass_to_dict() should be called on dataclass instances only.")

    result = asdict(instance)
    result["_type"] = instance.type

    for key, value in result.items():
        if isinstance(value, list):
            result[key] = [dataclass_to_dict(item) if is_dataclass(item) else item for item in value]
        elif is_dataclass(value):
            result[key] = dataclass_to_dict(value)

    return result
