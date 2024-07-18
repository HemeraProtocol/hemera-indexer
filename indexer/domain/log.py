from dataclasses import dataclass
from typing import Optional

from hexbytes import HexBytes

from common.models.logs import Logs
from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain


@dataclass
class Log(Domain):
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


def format_log_data(log_dict):
    log = {
        'model': Logs,
        'log_index': to_int(hexstr=log_dict['logIndex']),
        'address': to_normalized_address(log_dict['address']),
        'data': log_dict['data'],
        'topic0': log_dict['topics'][0] if len(log_dict['topics']) > 0 else None,
        'topic1': log_dict['topics'][1] if len(log_dict['topics']) > 1 else None,
        'topic2': log_dict['topics'][2] if len(log_dict['topics']) > 2 else None,
        'topic3': log_dict['topics'][3] if len(log_dict['topics']) > 3 else None,
        'transaction_hash': log_dict['transactionHash'],
        'transaction_index': to_int(hexstr=log_dict['transactionIndex']),
        'block_number': to_int(hexstr=log_dict['blockNumber']),
        'block_hash': log_dict['blockHash'],
        'block_timestamp': log_dict['blockTimestamp']
    }
    return log
