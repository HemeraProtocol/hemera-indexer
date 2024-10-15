import json
from dataclasses import dataclass
from typing import Dict, List, cast

from web3.types import ABIEvent

from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.transaction import Transaction
from indexer.utils.abi import event_log_abi_to_topic
from common.utils.abi_code_utils import decode_log

OPENSEA_EVENT_ABIS = {
    "ORDER_FULFILLED_EVENT": '{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"offerer","type":"address"},{"indexed":true,"internalType":"address","name":"zone","type":"address"},{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"indexed":false,"internalType":"struct SpentItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"indexed":false,"internalType":"struct ReceivedItem[]","name":"consideration","type":"tuple[]"}],"name":"OrderFulfilled","type":"event"}'
}

OPENSEA_EVENT_ABI_MAPPING: Dict[str, ABIEvent] = {
    key: cast(ABIEvent, json.loads(value)) for key, value in OPENSEA_EVENT_ABIS.items()
}

OPENSEA_EVENT_ABI_SIGNATURE_MAPPING: Dict[str, str] = {
    name: event_log_abi_to_topic(abi) for name, abi in OPENSEA_EVENT_ABI_MAPPING.items()
}


@dataclass
class OpenseaLog:
    orderHash: str
    offerer: str
    zone: str
    recipient: str
    offer: Dict[str, str]
    consideration: Dict[str, str]
    block_timestamp: int
    block_hash: str
    block_number: int
    transaction_hash: str
    log_index: int
    protocol_version: str = "1.6"

    fee_addresses: List[str] = None


def parse_opensea_transaction_order_fulfilled_event(
    transaction: Transaction, contract_address: str, protocol_version: str = 1.6, fee_addresses: List[str] = []
) -> List[OpenseaLog]:
    results = []
    logs = transaction.receipt.logs
    for log in logs:
        if (
            log.topic0 == OPENSEA_EVENT_ABI_SIGNATURE_MAPPING["ORDER_FULFILLED_EVENT"]
            and log.address == contract_address
        ):
            opensea_transaction = decode_log(OPENSEA_EVENT_ABI_MAPPING["ORDER_FULFILLED_EVENT"], log)

            results.append(
                OpenseaLog(
                    orderHash=bytes_to_hex_str(opensea_transaction["orderHash"]),
                    offerer=opensea_transaction["offerer"],
                    zone=opensea_transaction["zone"],
                    recipient=opensea_transaction["recipient"],
                    offer=opensea_transaction["offer"],
                    consideration=opensea_transaction["consideration"],
                    block_timestamp=transaction.block_timestamp,
                    block_hash=transaction.block_hash,
                    block_number=transaction.block_number,
                    transaction_hash=transaction.hash,
                    log_index=log.log_index,
                    protocol_version=protocol_version,
                    fee_addresses=fee_addresses,
                )
            )

    return results
