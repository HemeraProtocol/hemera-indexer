import json
from typing import List, cast

from eth_typing import ABIEvent, ABIFunction, HexStr
from web3._utils.contracts import decode_transaction_data

from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.utils.abi import event_log_abi_to_topic, function_abi_to_4byte_selector_str
from hemera_udf.deposit_to_l2.domains import TokenDepositTransaction

ETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

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

DEPOSIT_ETH_TO_ARBI_FUNCTION_SIG = "0x439370b1"

OUT_BOUND_TRANSFER_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"name":"_l1Token","type":"address","internalType":"address"},{"name":"_to","type":"address","internalType":"address"},{"name":"_amount","type":"uint256","internalType":"uint256"},{"name":"_maxGas","type":"uint256","internalType":"uint256"},{"name":"_gasPriceBid","type":"uint256","internalType":"uint256"},{"name":"_data","type":"bytes","internalType":"bytes"}],"name":"outboundTransfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}"""
    ),
)
OUT_BOUND_TRANSFER_FUNCTION_SIG = function_abi_to_4byte_selector_str(OUT_BOUND_TRANSFER_FUNCTION)

DEPOSIT_ETH_TO_LINEA_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_fee","type":"uint256"},{"internalType":"bytes","name":"_calldata","type":"bytes"}],"name":"sendMessage","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
DEPOSIT_ETH_TO_LINEA_FUNCTION_SIG = function_abi_to_4byte_selector_str(DEPOSIT_ETH_TO_LINEA_FUNCTION)

BRIDGE_TOKEN_TO_LINEA_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"address","name":"_l1Token","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"address","name":"_recipient","type":"address"}],"name":"bridgeToken","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
BRIDGE_TOKEN_TO_LINEA_FUNCTION_SIG = function_abi_to_4byte_selector_str(BRIDGE_TOKEN_TO_LINEA_FUNCTION)

DEPOSIT_USDC_TO_LINEA_FUNCTION = cast(
    ABIFunction,
    json.loads(
        """{"inputs":[{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"address","name":"_to","type":"address"}],"name":"depositTo","outputs":[],"stateMutability":"payable","type":"function"}"""
    ),
)
DEPOSIT_USDC_TO_LINEA_FUNCTION_SIG = function_abi_to_4byte_selector_str(DEPOSIT_USDC_TO_LINEA_FUNCTION)


def eth_deposit_parse(transaction: Transaction, chain_mapping: dict, function: ABIFunction) -> TokenDepositTransaction:
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=ETH_ADDRESS,
        value=transaction.value,
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


def usdc_deposit_parse(transaction: Transaction, chain_mapping: dict, function: ABIFunction) -> TokenDepositTransaction:
    decoded_input = decode_transaction_data(function, HexStr(transaction.input))
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=USDC_ADDRESS,
        value=decoded_input["_amount"],
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


def token_deposit_parse(
    transaction: Transaction, chain_mapping: dict, function: ABIFunction
) -> TokenDepositTransaction:
    decoded_input = decode_transaction_data(function, HexStr(transaction.input))
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=decoded_input["_l1Token"],
        value=decoded_input["_amount"],
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


token_parse_mapping = {
    "eth": eth_deposit_parse,
    "usdc": usdc_deposit_parse,
    "_l1Token": token_deposit_parse,
}


def parse_deposit_transaction_function(
    transactions: List[Transaction],
    contract_set: set,
    chain_mapping: dict,
    sig_function_mapping: dict,
    sig_parse_mapping: dict,
) -> List[TokenDepositTransaction]:
    deposit_tokens = []
    for transaction in transactions:
        if transaction.to_address in contract_set:
            input_sig = transaction.input[0:10]
            if input_sig in sig_function_mapping:
                deposit_transaction = sig_parse_mapping[input_sig](
                    transaction=transaction,
                    chain_mapping=chain_mapping,
                    function=sig_function_mapping[input_sig],
                )
                deposit_tokens.append(deposit_transaction)
    return deposit_tokens


if __name__ == "__main__":
    print(BRIDGE_ETH_TO_FUNCTION_SIG)
    print(DEPOSIT_ERC20_TO_FUNCTION_SIG)
    print(DEPOSIT_ETH_FUNCTION_SIG)
    print(DEPOSIT_ETH_TO_LINEA_FUNCTION_SIG)
    print(BRIDGE_TOKEN_TO_LINEA_FUNCTION_SIG)
    print(DEPOSIT_USDC_TO_LINEA_FUNCTION_SIG)
