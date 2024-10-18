from web3.types import ABIEvent

from common.utils.abi_code_utils import Event
from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.log import Log
from indexer.modules.custom.cyber_id.constants.constans import *
from indexer.modules.custom.cyber_id.domains.cyber_domain import CyberIDRegisterD, CyberAddressChangedD
from indexer.modules.custom.cyber_id.utils import get_node


class CyberEvent(Event):
    def __init__(self, event_abi: ABIEvent):
        super().__init__(event_abi)

    def process(self, log: Log):
        pass


class RegisterCyberEvent(CyberEvent):
    def __init__(self):
        super().__init__({
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
                {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
                {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
                {"indexed": False, "internalType": "string", "name": "cid", "type": "string"},
                {"indexed": False, "internalType": "uint256", "name": "cost", "type": "uint256"}
            ],
            "name": "Register",
            "type": "event"
        })

    def process(self, log: Log):
        if log.address.lower() != CyberIdTokenContractAddress:
            return None
        decode_data = self.decode_log(log)
        return [CyberIDRegisterD(
            label=decode_data['cid'],
            token_id=log.topic3,
            cost=int(decode_data['cost']),
            block_number=log.block_number,
            node=get_node(decode_data['cid'] + ".cyber"),
            registration=log.block_timestamp,
        )]


class AddressChangedCyberEvent(CyberEvent):
    def __init__(self):
        super().__init__({
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "bytes32", "name": "node", "type": "bytes32"},
                {"indexed": False, "internalType": "uint256", "name": "coinType", "type": "uint256"},
                {"indexed": False, "internalType": "bytes", "name": "newAddress", "type": "bytes"}
            ],
            "name": "AddressChanged",
            "type": "event"
        })

    def process(self, log: Log):
        if log.address.lower() != CyberIdPublicResolverContractAddress:
            return None
        decode_data = self.decode_log(log)
        return [CyberAddressChangedD(
            node=log.topic1,
            address=bytes_to_hex_str(decode_data.get("newAddress")),
            block_number=log.block_number
        )]


RegisterEvent = RegisterCyberEvent()
AddressChangedEvent = AddressChangedCyberEvent()
