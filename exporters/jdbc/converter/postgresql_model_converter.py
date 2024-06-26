from datetime import timezone, datetime

from sqlalchemy import func


def convert_item(table, data, fixing=False):
    if table == "blocks":
        return convert_to_block(data, fixing)

    elif table == "transactions":
        return convert_to_transaction(data, fixing)

    elif table == "logs":
        return convert_to_log(data, fixing)

    elif table == "traces":
        return convert_to_trace(data, fixing)

    elif table == "contract_internal_transactions":
        return convert_to_contract_internal_transactions(data, fixing)

    elif table == "contracts":
        return convert_to_contract(data, fixing)

    elif table == "address_coin_balances":
        return convert_to_coin_balance(data, fixing)

    elif table == "erc20_token_transfers":
        return convert_to_erc20_token_transfer(data, fixing)

    elif table == "erc20_token_holders":
        return convert_to_erc20_token_holder(data, fixing)

    elif table == "erc721_token_transfers":
        return convert_to_erc721_token_transfer(data, fixing)

    elif table == "erc721_token_holders":
        return convert_to_erc721_token_holder(data, fixing)

    elif table == "erc721_token_id_changes":
        return convert_to_erc721_token_id_change(data, fixing)

    elif table == "erc721_token_id_details":
        return convert_to_erc721_token_id_detail(data, fixing)

    elif table == "erc1155_token_transfers":
        return convert_to_erc1155_token_transfer(data, fixing)

    elif table == "erc1155_token_holders":
        return convert_to_erc1155_token_holder(data, fixing)

    elif table == "erc1155_token_id_details":
        return convert_to_erc1155_token_id_detail(data, fixing)

    elif table == "tokens":
        return convert_to_tokens(data, fixing)

    elif table == "address_token_balances":
        return convert_to_token_balance(data, fixing)

    elif table == "block_ts_mapper":
        return convert_to_block_ts_mapper(data)

    else:
        return None


def convert_to_block(block, fixing=False):
    return {
        'hash': bytes.fromhex(block["hash"][2:]),
        'number': block["number"],
        'timestamp': func.to_timestamp(block["timestamp"]),
        'parent_hash': bytes.fromhex(block["parent_hash"][2:]),
        'nonce': bytes.fromhex(block["nonce"][2:]),
        'gas_limit': block["gas_limit"],
        'gas_used': block["gas_used"],
        'base_fee_per_gas': block["base_fee_per_gas"],
        'difficulty': block["difficulty"],
        'size': block["size"],
        'miner': bytes.fromhex(block["miner"][2:]),
        'sha3_uncles': bytes.fromhex(block["sha3_uncles"][2:]),
        'transactions_root': bytes.fromhex(block["transactions_root"][2:]),
        'transactions_count': block["transactions_count"],
        'state_root': bytes.fromhex(block["state_root"][2:]),
        'receipts_root': bytes.fromhex(block["receipts_root"][2:]),
        'extra_data': bytes.fromhex(block["extra_data"][2:]),
        'withdrawals_root': bytes.fromhex(block["withdrawals_root"][2:]) if block["withdrawals_root"] else None,
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_transaction(transaction, fixing=False):
    return {
        'hash': bytes.fromhex(transaction["hash"][2:]),
        'transaction_index': transaction["transaction_index"],
        'from_address': bytes.fromhex(transaction["from_address"][2:]) if transaction["from_address"] else None,
        'to_address': bytes.fromhex(transaction["to_address"][2:]) if transaction["to_address"] else None,
        'value': transaction["value"],
        'transaction_type': transaction["transaction_type"],
        'input': bytes.fromhex(transaction["input"][2:]),
        'nonce': transaction["nonce"],
        'block_hash': bytes.fromhex(transaction["block_hash"][2:]),
        'block_number': transaction["block_number"],
        'block_timestamp': func.to_timestamp(transaction["block_timestamp"]),
        'gas': transaction["gas"],
        'gas_price': transaction["gas_price"],
        'max_fee_per_gas': transaction["max_fee_per_gas"],
        'max_priority_fee_per_gas': transaction["max_priority_fee_per_gas"],
        'receipt_root': bytes.fromhex(transaction["receipt_root"][2:]) if transaction["receipt_root"] else None,
        'receipt_status': transaction["receipt_status"],
        'receipt_gas_used': transaction["receipt_gas_used"],
        'receipt_cumulative_gas_used': transaction["receipt_cumulative_gas_used"],
        'receipt_effective_gas_price': transaction["receipt_effective_gas_price"],
        'receipt_l1_fee': transaction["receipt_l1_fee"],
        'receipt_l1_fee_scalar': transaction["receipt_l1_fee_scalar"],
        'receipt_l1_gas_used': transaction["receipt_l1_gas_used"],
        'receipt_l1_gas_price': transaction["receipt_l1_gas_price"],
        'blob_versioned_hashes': [bytes.fromhex(_[2:]) for _ in transaction["blob_versioned_hashes"]]
        if transaction["blob_versioned_hashes"] else None,
        'receipt_contract_address': bytes.fromhex(transaction["receipt_contract_address"][2:])
        if transaction["receipt_contract_address"] else None,
        'exist_error': transaction["exist_error"],
        'error': transaction["error"],
        'revert_reason': transaction["revert_reason"],
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_log(log, fixing=False):
    return {
        'log_index': log["log_index"],
        'address': bytes.fromhex(log["address"][2:]),
        'data': bytes.fromhex(log["data"][2:]),
        'topic0': bytes.fromhex(log["topic0"][2:]) if log["topic1"] else None,
        'topic1': bytes.fromhex(log["topic1"][2:]) if log["topic1"] else None,
        'topic2': bytes.fromhex(log["topic2"][2:]) if log["topic2"] else None,
        'topic3': bytes.fromhex(log["topic3"][2:]) if log["topic3"] else None,
        'transaction_hash': bytes.fromhex(log["transaction_hash"][2:]),
        'transaction_index': log["transaction_index"],
        'block_number': log["block_number"],
        'block_hash': bytes.fromhex(log["block_hash"][2:]),
        'block_timestamp': func.to_timestamp(log["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_tokens(token, fixing=False):
    return {
        "address": bytes.fromhex(token["address"][2:]),
        'name': token['name'],
        'symbol': token['symbol'],
        'total_supply': token['total_supply'],
        'decimals': token['decimals'],
        'token_type': token['token_type'],
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
    }


def convert_to_erc20_token_transfer(token_transfer, fixing=False):
    return {
        'transaction_hash': bytes.fromhex(token_transfer["transaction_hash"][2:]),
        'log_index': token_transfer["log_index"],
        "from_address": bytes.fromhex(token_transfer["from_address"][2:]),
        "to_address": bytes.fromhex(token_transfer["to_address"][2:]),
        "token_address": bytes.fromhex(token_transfer["token_address"][2:]),
        "value": token_transfer["value"],
        'block_number': token_transfer["block_number"],
        'block_hash': bytes.fromhex(token_transfer["block_hash"][2:]),
        'block_timestamp': func.to_timestamp(token_transfer["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc20_token_holder(token_holder, fixing=False):
    return {
        "token_address": bytes.fromhex(token_holder["token_address"][2:]),
        "wallet_address": bytes.fromhex(token_holder["wallet_address"][2:]),
        "balance_of": token_holder["balance_of"],
        'block_number': token_holder["block_number"],
        'block_timestamp': func.to_timestamp(token_holder["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc721_token_transfer(token_transfer, fixing=False):
    return {
        'transaction_hash': bytes.fromhex(token_transfer["transaction_hash"][2:]),
        'log_index': token_transfer["log_index"],
        "from_address": bytes.fromhex(token_transfer["from_address"][2:]),
        "to_address": bytes.fromhex(token_transfer["to_address"][2:]),
        "token_address": bytes.fromhex(token_transfer["token_address"][2:]),
        "token_id": token_transfer["token_id"],
        'block_number': token_transfer["block_number"],
        'block_hash': bytes.fromhex(token_transfer["block_hash"][2:]),
        'block_timestamp': func.to_timestamp(token_transfer["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc721_token_holder(token_holder, fixing=False):
    return {
        "token_address": bytes.fromhex(token_holder["token_address"][2:]),
        "wallet_address": bytes.fromhex(token_holder["wallet_address"][2:]),
        "balance_of": token_holder["balance_of"],
        'block_number': token_holder["block_number"],
        'block_timestamp': func.to_timestamp(token_holder["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc721_token_id_change(token_id_change, fixing=False):
    return {
        "address": bytes.fromhex(token_id_change["address"][2:]),
        "token_id": token_id_change["token_id"],
        "token_owner": bytes.fromhex(token_id_change["token_owner"][2:]) if token_id_change["token_owner"] else None,
        'block_number': token_id_change["block_number"],
        'block_timestamp': func.to_timestamp(token_id_change["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc721_token_id_detail(token_id_detail, fixing=False):
    return {
        "address": bytes.fromhex(token_id_detail["address"][2:]),
        "token_id": token_id_detail["token_id"],
        "token_owner": bytes.fromhex(token_id_detail["token_owner"][2:]) if token_id_detail["token_owner"] else None,
        "token_uri": token_id_detail["token_uri"],
        "token_uri_info": token_id_detail["token_uri_info"],
        'block_number': token_id_detail["block_number"],
        'block_timestamp': func.to_timestamp(token_id_detail["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc1155_token_transfer(token_transfer, fixing=False):
    return {
        'transaction_hash': bytes.fromhex(token_transfer["transaction_hash"][2:]),
        'log_index': token_transfer["log_index"],
        "from_address": bytes.fromhex(token_transfer["from_address"][2:]),
        "to_address": bytes.fromhex(token_transfer["to_address"][2:]),
        "token_address": bytes.fromhex(token_transfer["token_address"][2:]),
        "token_id": token_transfer["token_id"],
        "value": token_transfer["value"],
        'block_number': token_transfer["block_number"],
        'block_hash': bytes.fromhex(token_transfer["block_hash"][2:]),
        'block_timestamp': func.to_timestamp(token_transfer["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc1155_token_holder(token_holder, fixing=False):
    return {
        "token_address": bytes.fromhex(token_holder["token_address"][2:]),
        "wallet_address": bytes.fromhex(token_holder["wallet_address"][2:]),
        "token_id": token_holder["token_id"],
        "balance_of": token_holder["balance_of"],
        "latest_call_contract_time": func.to_timestamp(token_holder["latest_call_contract_time"]),
        'block_number': token_holder["block_number"],
        'block_timestamp': func.to_timestamp(token_holder["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_erc1155_token_id_detail(token_id_detail, fixing=False):
    return {
        "address": bytes.fromhex(token_id_detail["address"][2:]),
        "token_id": token_id_detail["token_id"],
        "token_supply": token_id_detail["token_supply"],
        "token_uri": token_id_detail["token_uri"],
        "token_uri_info": token_id_detail["token_uri_info"],
        'block_number': token_id_detail["block_number"],
        'block_timestamp': func.to_timestamp(token_id_detail["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_token_balance(token_balance, fixing=False):
    return {
        'address': bytes.fromhex(token_balance["address"][2:]),
        "token_id": token_balance["token_id"],
        "token_type": token_balance["token_type"],
        "token_address": bytes.fromhex(token_balance["token_address"][2:]),
        "balance": token_balance["balance"],
        'block_number': token_balance["block_number"],
        'block_timestamp': func.to_timestamp(token_balance["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_trace(trace, fixing=False):
    return {
        "trace_id": trace["trace_id"],
        "from_address": bytes.fromhex(trace["from_address"][2:]) if trace["from_address"] else None,
        "to_address": bytes.fromhex(trace["to_address"][2:]) if trace["to_address"] else None,
        "value": trace["value"],
        "input": bytes.fromhex(trace["input"][2:]) if trace["input"] else None,
        "output": bytes.fromhex(trace["output"][2:]) if trace["output"] else None,
        "trace_type": trace["trace_type"],
        "call_type": trace["call_type"],
        "gas": trace["gas"],
        "gas_used": trace["gas_used"],
        "subtraces": trace["subtraces"],
        "trace_address": trace["trace_address"],
        "error": trace["error"],
        "status": trace["status"],
        'block_number': trace["block_number"],
        'block_hash': bytes.fromhex(trace["block_hash"][2:]) if trace["block_hash"] else None,
        'block_timestamp': func.to_timestamp(trace["block_timestamp"]),
        'transaction_index': trace["transaction_index"],
        'transaction_hash': bytes.fromhex(trace["transaction_hash"][2:]) if trace["transaction_hash"] else None,
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_contract_internal_transactions(internal_transactions, fixing=False):
    return {
        "trace_id": internal_transactions["trace_id"],
        "from_address": bytes.fromhex(internal_transactions["from_address"][2:]) if internal_transactions[
            "from_address"] else None,
        "to_address": bytes.fromhex(internal_transactions["to_address"][2:]) if internal_transactions[
            "to_address"] else None,
        "value": internal_transactions["value"],
        "trace_type": internal_transactions["trace_type"],
        "call_type": internal_transactions["call_type"],
        "gas": internal_transactions["gas"],
        "gas_used": internal_transactions["gas_used"],
        "trace_address": internal_transactions["trace_address"],
        "error": internal_transactions["error"],
        "status": internal_transactions["status"],
        'block_number': internal_transactions["block_number"],
        'block_hash': bytes.fromhex(internal_transactions["block_hash"][2:]) if internal_transactions[
            "block_hash"] else None,
        'block_timestamp': func.to_timestamp(internal_transactions["block_timestamp"]),
        'transaction_index': internal_transactions["transaction_index"],
        'transaction_hash': bytes.fromhex(internal_transactions["transaction_hash"][2:]) if internal_transactions[
            "transaction_hash"] else None,
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_contract(contract, fixing=False):
    return {
        'address': bytes.fromhex(contract['address'][2:]),
        'name': contract['name'],
        'contract_creator': bytes.fromhex(contract['contract_creator'][2:]),
        'creation_code': bytes.fromhex(contract['creation_code'][2:]),
        'deployed_code': bytes.fromhex(contract['deployed_code'][2:]),
        'block_number': contract['block_number'],
        'block_hash': bytes.fromhex(contract['block_hash'][2:]),
        'block_timestamp': func.to_timestamp(contract["block_timestamp"]),
        'transaction_index': contract['transaction_index'],
        'transaction_hash': bytes.fromhex(contract['transaction_hash'][2:]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_coin_balance(coin_balance, fixing=False):
    return {
        'address': bytes.fromhex(coin_balance['address'][2:]),
        'balance': coin_balance['balance'],
        'block_number': coin_balance["block_number"],
        'block_timestamp': func.to_timestamp(coin_balance["block_timestamp"]),
        'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if fixing else None,
        'relog': False
    }


def convert_to_block_ts_mapper(mapper):
    return {
        "ts": mapper["timestamp"],
        "block_number": mapper["block_number"],
        "timestamp": func.to_timestamp(mapper["timestamp"]),
    }
