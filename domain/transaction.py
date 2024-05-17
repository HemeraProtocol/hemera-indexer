from exporters.jdbc.schema.transactions import Transactions
from utils.utils import hex_to_dec, to_normalized_address


def format_transaction_data(transaction_dict):
    transaction = {
        'model': Transactions,
        'hash': transaction_dict['hash'],
        'transaction_index': hex_to_dec(transaction_dict['transactionIndex']),
        'from_address': to_normalized_address(transaction_dict['from']),
        'to_address': to_normalized_address(transaction_dict['to']),
        'value': hex_to_dec(transaction_dict['value']),
        'transaction_type': hex_to_dec(transaction_dict['type']),
        'input': transaction_dict['input'],
        'nonce': hex_to_dec(transaction_dict['nonce']),
        'block_hash': transaction_dict['blockHash'],
        'block_number': hex_to_dec(transaction_dict['blockNumber']),
        'block_timestamp': hex_to_dec(transaction_dict['blockTimestamp']),
        'gas': hex_to_dec(transaction_dict['gas']),
        'gas_price': hex_to_dec(transaction_dict['gasPrice']),
        'max_fee_per_gas': hex_to_dec(transaction_dict.get('maxFeePerGas')),
        'max_priority_fee_per_gas': hex_to_dec(transaction_dict.get('maxPriorityFeePerGas')),

        'receipt_gas_used': hex_to_dec(transaction_dict.get('receiptGasUsed')),
        'receipt_cumulative_gas_used': hex_to_dec(transaction_dict.get('receiptCumulativeGasUsed')),
        'receipt_effective_gas_price': hex_to_dec(transaction_dict.get('receiptEffectiveGasPrice')),
        'receipt_root': to_normalized_address(transaction_dict.get('receiptRoot')),
        'receipt_status': hex_to_dec(transaction_dict.get('receiptStatus')),
        'receipt_l1_fee': hex_to_dec(transaction_dict.get('receiptL1Fee')),
        'receipt_l1_fee_scalar': hex_to_dec(transaction_dict.get('receiptL1FeeScalar')),
        'receipt_l1_gas_used': hex_to_dec(transaction_dict.get('receiptL1GasUsed')),
        'receipt_l1_gas_price': hex_to_dec(transaction_dict.get('receiptL1GasPrice')),
        'receipt_blob_gas_used': hex_to_dec(transaction_dict.get('receiptBlobGasUsed')),
        'receipt_blob_gas_price': hex_to_dec(transaction_dict.get('receiptBlobGasPrice')),
        'blob_versioned_hashes': transaction_dict.get('blobVersionedHashes'),
        'receipt_contract_address': to_normalized_address(transaction_dict.get('receiptContractAddress')),

        # may occur KeyError, should check and fix later
        'exist_error': True if transaction_dict.get('error') is not None else False,
        'error': transaction_dict.get('error'),
        'revert_reason': transaction_dict.get('revertReason'),
    }

    return transaction
