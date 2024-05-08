from utils.utils import hex_to_dec, to_normalized_address


class EthTransaction(object):
    def __init__(self):
        self.hash = None
        self.transaction_index = None
        self.from_address = None
        self.to_address = None
        self.value = None
        self.transaction_type = None
        self.input = None
        self.nonce = None
        self.block_hash = None
        self.block_number = None
        self.block_timestamp = None
        self.gas = None
        self.gas_price = None
        self.max_fee_per_gas = None
        self.max_priority_fee_per_gas = None
        self.receipt_gas_used = None
        self.receipt_cumulative_gas_used = None
        self.receipt_effective_gas_price = None
        self.receipt_root = None
        self.receipt_status = None
        self.receipt_l1_fee = None
        self.receipt_l1_fee_scalar = None
        self.receipt_l1_gas_used = None
        self.receipt_l1_gas_price = None
        self.receipt_blob_gas_used = None
        self.receipt_blob_gas_price = None
        self.blob_versioned_hashes = []
        self.receipt_contract_address = None
        self.exist_error = False
        self.error = None
        self.revert_reason = None

    def __str__(self):
        return (f"Transaction(hash: {self.hash}, transaction_index: {self.transaction_index}, from_address: {self.from_address}, \n"
                f"to_address: {self.to_address}, value: {self.value}, transaction_type: {self.transaction_type}, input: {self.input}, \n"
                f"nonce: {self.nonce}, block_hash: {self.block_hash}, block_number: {self.block_number}, block_timestamp: {self.block_timestamp}, \n"
                f"gas: {self.gas}, gas_price: {self.gas_price}, max_fee_per_gas: {self.max_fee_per_gas}, max_priority_fee_per_gas: {self.max_priority_fee_per_gas}, \n"
                f"receipt_gas_used: {self.receipt_gas_used}, receipt_cumulative_gas_used: {self.receipt_cumulative_gas_used}, \n"
                f"receipt_effective_gas_price: {self.receipt_effective_gas_price}, receipt_root: {self.receipt_root}, \n"
                f"receipt_status: {self.receipt_status}, receipt_l1_fee: {self.receipt_l1_fee}, receipt_l1_fee_scalar: {self.receipt_l1_fee_scalar}, \n"
                f"receipt_l1_gas_used: {self.receipt_gas_used}, receipt_l1_gas_price: {self.receipt_l1_gas_price}, \n"
                f"receipt_blob_gas_used: {self.receipt_blob_gas_used}, receipt_blob_gas_price: {self.receipt_blob_gas_price}, \n"
                f"blob_versioned_hashes: {self.blob_versioned_hashes}, \n"
                f"receipt_contract_address: {self.receipt_contract_address}, \n"
                f"exist_error: {self.exist_error}, error: {self.error}, revert_reason: {self.revert_reason} \n)")



def transfer_dict_to_transaction(transaction_dict):
    transaction = EthTransaction()
    transaction.hash = transaction_dict['hash']
    transaction.transaction_index = hex_to_dec(transaction_dict['transactionIndex'])
    transaction.from_address = to_normalized_address(transaction_dict['from'])
    transaction.to_address = to_normalized_address(transaction_dict['to'])
    transaction.value = hex_to_dec(transaction_dict['value'])
    transaction.transaction_type = hex_to_dec(transaction_dict['type'])
    transaction.input = transaction_dict['input']
    transaction.nonce = hex_to_dec(transaction_dict['nonce'])
    transaction.block_hash = transaction_dict['blockHash']
    transaction.block_number = hex_to_dec(transaction_dict['blockNumber'])
    # transaction.block_timestamp = hex_to_dec(transaction_dict['blockTimestamp'])
    transaction.gas = hex_to_dec(transaction_dict['gas'])
    transaction.gas_price = hex_to_dec(transaction_dict['gasPrice'])
    transaction.max_fee_per_gas = hex_to_dec(transaction_dict.get('maxFeePerGas'))
    transaction.max_priority_fee_per_gas = hex_to_dec(transaction_dict.get('maxPriorityFeePerGas'))

    # may occur KeyError, should check and fix later
    transaction.receipt_gas_used = hex_to_dec(transaction_dict.get('receiptGasUsed'))
    transaction.receipt_cumulative_gas_used = hex_to_dec(transaction_dict.get('receiptCumulativeGasUsed'))
    transaction.receipt_effective_gas_price = hex_to_dec(transaction_dict.get('receiptEffectiveGasPrice'))
    transaction.receipt_root = to_normalized_address(transaction_dict.get('receiptRoot'))
    transaction.receipt_status = transaction_dict.get('receiptStatus')
    transaction.receipt_l1_fee = hex_to_dec(transaction_dict.get('receiptL1Fee'))
    transaction.receipt_l1_fee_scalar = hex_to_dec(transaction_dict.get('receiptL1FeeScalar'))
    transaction.receipt_l1_gas_used = hex_to_dec(transaction_dict.get('receiptL1GasUsed'))
    transaction.receipt_l1_gas_price = hex_to_dec(transaction_dict.get('receiptL1GasPrice'))
    transaction.receipt_blob_gas_used = hex_to_dec(transaction_dict.get('receiptBlobGasUsed'))
    transaction.receipt_blob_gas_price = hex_to_dec(transaction_dict.get('receiptBlobGasPrice'))
    transaction.blob_versioned_hashes = transaction_dict.get('blobVersionedHashes')
    transaction.receipt_contract_address = to_normalized_address(transaction_dict.get('receiptContractAddress'))
    transaction.exist_error = True if transaction_dict.get('error') is not None else False
    transaction.error = transaction_dict.get('error')
    transaction.revert_reason = transaction_dict.get('revertReason')

    return transaction
