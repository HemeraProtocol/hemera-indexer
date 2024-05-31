from exporters.jdbc.schema.contract_internal_transactions import ContractInternalTransactions


def trace_to_contract_internal_transaction(enriched_trace):
    contract_internal_transaction = {
        'model': ContractInternalTransactions,
        'trace_id': enriched_trace['trace_id'],
        'from_address': enriched_trace['from_address'],
        'to_address': enriched_trace['to_address'],
        'value': enriched_trace['value'],
        'trace_type': enriched_trace['trace_type'],
        'call_type': enriched_trace['call_type'],
        'gas': enriched_trace['gas'],
        'gas_used': enriched_trace['gas_used'],
        'trace_address': enriched_trace['trace_address'],
        'error': enriched_trace['error'],
        'status': enriched_trace['status'],
        'block_number': enriched_trace['block_number'],
        'block_hash': enriched_trace['block_hash'],
        'block_timestamp': enriched_trace['block_timestamp'],
        'transaction_index': enriched_trace['transaction_index'],
        'transaction_hash': enriched_trace['transaction_hash'],
        'trace_index': enriched_trace['trace_index'],
    }

    return contract_internal_transaction
