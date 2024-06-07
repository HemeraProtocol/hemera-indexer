from exporters.jdbc.schema.transactions import Transactions
from eth_utils import to_int, to_normalized_address


def format_transaction_data(transaction_dict):
    transaction = {
        'model': Transactions,
        'hash': transaction_dict['hash'],
        'transaction_index': to_int(hexstr=transaction_dict['transactionIndex']),
        'from_address': to_normalized_address(transaction_dict['from']),
        'to_address': to_normalized_address(transaction_dict['to']) if transaction_dict['to'] else None,
        'value': to_int(hexstr=transaction_dict['value']),
        'transaction_type': to_int(hexstr=transaction_dict['type']),
        'input': transaction_dict['input'],
        'nonce': to_int(hexstr=transaction_dict['nonce']),
        'block_hash': transaction_dict['blockHash'],
        'block_number': to_int(hexstr=transaction_dict['blockNumber']),
        'block_timestamp': to_int(hexstr=transaction_dict['blockTimestamp']),
        'gas': to_int(hexstr=transaction_dict['gas']),
        'gas_price': to_int(hexstr=transaction_dict['gasPrice']),
        'max_fee_per_gas': to_int(hexstr=transaction_dict.get('maxFeePerGas'))
        if transaction_dict['maxFeePerGas'] else None,
        'max_priority_fee_per_gas': to_int(hexstr=transaction_dict.get('maxPriorityFeePerGas'))
        if transaction_dict['maxPriorityFeePerGas'] else None,

        'receipt_gas_used': to_int(hexstr=transaction_dict.get('receiptGasUsed'))
        if transaction_dict.get('receiptGasUsed') else None,
        'receipt_cumulative_gas_used': to_int(hexstr=transaction_dict.get('receiptCumulativeGasUsed'))
        if transaction_dict.get('receiptCumulativeGasUsed') else None,
        'receipt_effective_gas_price': to_int(hexstr=transaction_dict.get('receiptEffectiveGasPrice'))
        if transaction_dict.get('receiptEffectiveGasPrice') else None,
        'receipt_root': to_normalized_address(transaction_dict.get('receiptRoot'))
        if transaction_dict.get('receiptRoot') else None,
        'receipt_status': to_int(hexstr=transaction_dict.get('receiptStatus'))
        if transaction_dict.get('receiptStatus') else None,
        'receipt_l1_fee': to_int(hexstr=transaction_dict.get('receiptL1Fee'))
        if transaction_dict.get('receiptL1Fee') else None,
        'receipt_l1_fee_scalar': to_int(hexstr=transaction_dict.get('receiptL1FeeScalar'))
        if transaction_dict.get('receiptL1FeeScalar') else None,
        'receipt_l1_gas_used': to_int(hexstr=transaction_dict.get('receiptL1GasUsed'))
        if transaction_dict.get('receiptL1GasUsed') else None,
        'receipt_l1_gas_price': to_int(hexstr=transaction_dict.get('receiptL1GasPrice'))
        if transaction_dict.get('receiptL1GasPrice') else None,
        'receipt_blob_gas_used': to_int(hexstr=transaction_dict.get('receiptBlobGasUsed'))
        if transaction_dict.get('receiptBlobGasUsed') else None,
        'receipt_blob_gas_price': to_int(hexstr=transaction_dict.get('receiptBlobGasPrice'))
        if transaction_dict.get('receiptBlobGasUsed') else None,
        'blob_versioned_hashes': transaction_dict.get('blobVersionedHashes')
        if transaction_dict.get('blobVersionedHashes') else None,
        'receipt_contract_address': to_normalized_address(transaction_dict.get('receiptContractAddress'))
        if transaction_dict.get('receiptContractAddress') else None,

        # may occur KeyError, should check and fix later
        'exist_error': True if transaction_dict.get('error') is not None else False,
        'error': transaction_dict.get('error'),
        'revert_reason': transaction_dict.get('revertReason'),
    }

    return transaction
