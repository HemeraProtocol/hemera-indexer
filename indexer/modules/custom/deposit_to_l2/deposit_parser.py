from typing import List

from common.utils.abi_code_utils import Function
from indexer.domain.transaction import Transaction
from indexer.modules.custom.deposit_to_l2.domains.token_deposit_transaction import TokenDepositTransaction

ETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def eth_deposit_parse(transaction: Transaction, chain_mapping: dict, function: Function) -> TokenDepositTransaction:
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


def usdc_deposit_parse(transaction: Transaction, chain_mapping: dict, function: Function) -> TokenDepositTransaction:
    decoded_input = function.decode_function_input_data(transaction.input)
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


def token_deposit_parse(transaction: Transaction, chain_mapping: dict, function: Function) -> TokenDepositTransaction:
    decoded_input = function.decode_function_input_data(transaction.input)
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
    pass
