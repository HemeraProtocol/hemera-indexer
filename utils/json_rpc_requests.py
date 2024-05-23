def generate_get_block_by_number_json_rpc(block_numbers, include_transactions):
    for idx, block_number in enumerate(block_numbers):
        yield generate_json_rpc(
            method='eth_getBlockByNumber',
            params=[hex(block_number), include_transactions],
            request_id=idx
        )


def generate_trace_block_by_number_json_rpc(block_numbers):
    for block_number in block_numbers:
        yield generate_json_rpc(
            method='debug_traceBlockByNumber',
            params=[hex(block_number), {'tracer': 'callTracer'}],
            # save block_number in request ID, so later we can identify block number in response
            request_id=block_number,
        )


def generate_get_receipt_json_rpc(transaction_hashes):
    for idx, transaction_hash in enumerate(transaction_hashes):
        yield generate_json_rpc(
            method='eth_getTransactionReceipt',
            params=[transaction_hash],
            request_id=idx
        )


def generate_get_code_json_rpc(contract_addresses, block='latest'):
    for idx, contract_address in enumerate(contract_addresses):
        yield generate_json_rpc(
            method='eth_getCode',
            params=[contract_address, hex(block) if isinstance(block, int) else block],
            request_id=idx
        )


def generate_get_balance_json_rpc(coin_addresses):
    for idx, coin_address in enumerate(coin_addresses):
        yield generate_json_rpc(
            method='eth_getBalance',
            params=[coin_address['address'], coin_address['block_number']],
            request_id=idx
        )


def generate_get_token_balance_json_rpc(parameters):
    for idx, parameter in enumerate(parameters):
        yield generate_json_rpc(
            method='eth_call',
            params=[{'to': parameter['token_address'], 'data': parameter['data']}, parameter['block_number']],
            request_id=idx
        )


def generate_json_rpc(method, params, request_id=1):
    return {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': request_id,
    }

def generate_contract_object(token_address, token_type):
    pass

