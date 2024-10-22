from web3.types import ABIFunction

from common.utils.abi_code_utils import Function
from indexer.domain.transaction import Transaction
from indexer.modules.custom.cyber_id.domains.cyber_domain import CyberAddressD
from indexer.modules.custom.cyber_id.utils import get_reverse_node


class CyberFunction(Function):
    def __init__(self, function_abi: ABIFunction):
        super().__init__(function_abi)

    def process(self, transaction: Transaction, **kwargs):
        pass


class SetNameForAddressCyberFunction(CyberFunction):
    def __init__(self):
        super().__init__(
            {
                "inputs": [
                    {"internalType": "address", "name": "addr", "type": "address"},
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "address", "name": "resolver", "type": "address"},
                    {"internalType": "string", "name": "name", "type": "string"},
                ],
                "name": "setNameForAddr",
                "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        )

    def process(self, transaction: Transaction, **kwargs):
        if transaction.to_address.lower() != kwargs.get("cyber_id_reverse_registrar_contract_address"):
            return None
        decoded_input = self.decode_data(transaction.input)
        cyber_address = CyberAddressD(
            address=decoded_input.get("addr").lower(),
            name=decoded_input.get("name"),
            block_number=transaction.block_number,
            reverse_node=get_reverse_node(decoded_input.get("addr")),
        )
        return [cyber_address]


class SetNameCyberFunction(CyberFunction):
    def __init__(self):
        super().__init__(
            {
                "inputs": [{"internalType": "string", "name": "name", "type": "string"}],
                "name": "setName",
                "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        )

    def process(self, transaction: Transaction, **kwargs):
        if transaction.to_address.lower() != kwargs.get("cyber_id_reverse_registrar_contract_address"):
            return None
        decoded_input = self.decode_data(transaction.input)
        cyber_address = CyberAddressD(
            address=transaction.from_address.lower(),
            name=decoded_input.get("name"),
            block_number=transaction.block_number,
            reverse_node=get_reverse_node(transaction.from_address),
        )
        return [cyber_address]


SetNameForAddrFunction = SetNameForAddressCyberFunction()
SetNameFunction = SetNameCyberFunction()
