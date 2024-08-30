import json
from dataclasses import dataclass
from typing import List, cast

from eth_typing import HexStr
from web3._utils.contracts import decode_transaction_data
from web3.types import ABIEvent, ABIFunction

from indexer.domain.transaction import Transaction
from indexer.utils.abi import event_log_abi_to_topic, function_abi_to_4byte_selector_str

ETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

ETH_DEPOSIT_INITIATED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"extraData","type":"bytes"}],"name":"ETHDepositInitiated","type":"event"}"""
    ),
)
ETH_DEPOSIT_INITIATED_EVENT_SIG = event_log_abi_to_topic(ETH_DEPOSIT_INITIATED_EVENT)

ETH_BRIDGE_INITIATED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"extraData","type":"bytes"}],"name":"ETHBridgeInitiated","type":"event"}"""
    ),
)
ETH_BRIDGE_INITIATED_EVENT_SIG = event_log_abi_to_topic(ETH_BRIDGE_INITIATED_EVENT)

TRANSACTION_DEPOSITED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"version","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"opaqueData","type":"bytes"}],"name":"TransactionDeposited","type":"event"}"""
    ),
)
TRANSACTION_DEPOSITED_EVENT_SIG = event_log_abi_to_topic(TRANSACTION_DEPOSITED_EVENT)

DEPOSIT_ETH_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"uint32","name":"_minGasLimit","type":"uint32"},{"internalType":"bytes","name":"_extraData","type":"bytes"}],"name":"depositETH","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
DEPOSIT_ETH_FUNCTION_SIG = function_abi_to_4byte_selector_str(DEPOSIT_ETH_FUNCTION)

BRIDGE_ETH_TO_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint32","name":"_minGasLimit","type":"uint32"},{"internalType":"bytes","name":"_extraData","type":"bytes"}],"name":"bridgeETHTo","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
BRIDGE_ETH_TO_FUNCTION_SIG = function_abi_to_4byte_selector_str(BRIDGE_ETH_TO_FUNCTION)

DEPOSIT_ERC20_TO_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"address","name":"_l1Token","type":"address"},{"internalType":"address","name":"_l2Token","type":"address"},{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"uint32","name":"_minGasLimit","type":"uint32"},{"internalType":"bytes","name":"_extraData","type":"bytes"}],"name":"depositERC20To","outputs":[],"stateMutability":"nonpayable","type":"function"}"""
    ),
)
DEPOSIT_ERC20_TO_FUNCTION_SIG = function_abi_to_4byte_selector_str(DEPOSIT_ERC20_TO_FUNCTION)

DEPOSIT_TRANSACTION_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_value","type":"uint256"},{"internalType":"uint64","name":"_gasLimit","type":"uint64"},{"internalType":"bool","name":"_isCreation","type":"bool"},{"internalType":"bytes","name":"_extraData","type":"bytes"}],"name":"depositTransaction","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
DEPOSIT_TRANSACTION_FUNCTION_SIG = function_abi_to_4byte_selector_str(DEPOSIT_TRANSACTION_FUNCTION)


@dataclass
class DepositToken:
    wallet_address: str
    chain: str
    contract_address: str
    token_address: str
    value: int
    block_number: int


def parse_deposit_transfer_function(
    transactions: List[Transaction], contract_set: set, chain_mapping: dict
) -> List[DepositToken]:
    deposit_tokens = []
    for transaction in transactions:
        if transaction.to_address in contract_set:
            input_sig = transaction.input[0:10]
            if input_sig == DEPOSIT_ETH_FUNCTION_SIG or input_sig == BRIDGE_ETH_TO_FUNCTION_SIG:
                deposit_tokens.append(
                    DepositToken(
                        wallet_address=transaction.from_address,
                        chain=chain_mapping[transaction.to_address],
                        contract_address=transaction.to_address,
                        token_address=ETH_ADDRESS,
                        value=transaction.value,
                        block_number=transaction.block_number,
                    )
                )
            elif input_sig == DEPOSIT_ERC20_TO_FUNCTION_SIG:
                decoded_input = decode_transaction_data(DEPOSIT_TRANSACTION_FUNCTION, HexStr(transaction.input))
                deposit_tokens.append(
                    DepositToken(
                        wallet_address=transaction.from_address,
                        chain=chain_mapping[transaction.to_address],
                        contract_address=transaction.to_address,
                        token_address=decoded_input["_l1Token"],
                        value=decoded_input["_amount"],
                        block_number=transaction.block_number,
                    )
                )
    return deposit_tokens


if __name__ == "__main__":
    print(ETH_DEPOSIT_INITIATED_EVENT_SIG)
    print(ETH_BRIDGE_INITIATED_EVENT_SIG)
    print(TRANSACTION_DEPOSITED_EVENT_SIG)
    print(BRIDGE_ETH_TO_FUNCTION_SIG)
    print(DEPOSIT_ERC20_TO_FUNCTION_SIG)
