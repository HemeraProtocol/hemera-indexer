from datetime import timezone, datetime

from sqlalchemy import func


class PostgreSQLModelConverter:

    def __init__(self, confirm):
        self.confirm = confirm

    def convert_item(self, data_type, data):

        if data_type == "blocks":
            return self.convert_to_block(data)

        elif data_type == "transactions":
            return self.convert_to_transaction(data)

        elif data_type == "logs":
            return self.convert_to_log(data)

        elif data_type == "traces":
            return self.convert_to_trace(data)

        elif data_type == "address_coin_balances":
            return self.convert_to_coin_balance(data)

        elif data_type == "token_transfers":
            return self.convert_to_token_transfer(data)

        elif data_type == "address_token_balances":
            return self.convert_to_token_balance(data)

        elif data_type == "block_ts_mapper":
            return self.convert_to_block_ts_mapper(data)

        else:
            return None

    def convert_to_block(self, block):
        return {
            'hash': bytes(block["hash"], 'utf-8'),
            'number': block["number"],
            'timestamp': func.to_timestamp(block["timestamp"]),
            'parent_hash': bytes(block["parent_hash"], 'utf-8'),
            'nonce': bytes(block["nonce"], 'utf-8'),
            'gas_limit': block["gas_limit"],
            'gas_used': block["gas_used"],
            'base_fee_per_gas': block["base_fee_per_gas"],
            'difficulty': block["difficulty"],
            'size': block["size"],
            'miner': bytes(block["miner"], 'utf-8'),
            'sha3_uncles': bytes(block["sha3_uncles"], 'utf-8'),
            'transactions_root': bytes(block["transactions_root"], 'utf-8'),
            'transactions_count': block["transactions_count"],
            'state_root': bytes(block["state_root"], 'utf-8'),
            'receipts_root': bytes(block["receipts_root"], 'utf-8'),
            'extra_data': bytes(block["extra_data"], 'utf-8'),
            'withdrawals_root': bytes(block["withdrawals_root"], 'utf-8') if block["withdrawals_root"] else None,
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
            'data_confirmed': self.confirm,
        }

    def convert_to_transaction(self, transaction):
        return {
            'hash': bytes(transaction["hash"], 'utf-8'),
            'transaction_index': transaction["transaction_index"],
            'from_address': bytes(transaction["from_address"], 'utf-8') if transaction["from_address"] else None,
            'to_address': bytes(transaction["to_address"], 'utf-8') if transaction["to_address"] else None,
            'value': transaction["value"],
            'transaction_type': transaction["transaction_type"],
            'input': bytes(transaction["input"], 'utf-8'),
            'nonce': transaction["nonce"],
            'block_hash': bytes(transaction["block_hash"], 'utf-8'),
            'block_number': transaction["block_number"],
            'block_timestamp': func.to_timestamp(transaction["block_timestamp"]),
            'gas': transaction["gas"],
            'gas_price': transaction["gas_price"],
            'max_fee_per_gas': transaction["max_fee_per_gas"],
            'max_priority_fee_per_gas': transaction["max_priority_fee_per_gas"],
            'receipt_root': bytes(transaction["receipt_root"], 'utf-8') if transaction["receipt_root"] else None,
            'receipt_status': transaction["receipt_status"],
            'receipt_gas_used': transaction["receipt_gas_used"],
            'receipt_cumulative_gas_used': transaction["receipt_cumulative_gas_used"],
            'receipt_effective_gas_price': transaction["receipt_effective_gas_price"],
            'receipt_l1_fee': transaction["receipt_l1_fee"],
            'receipt_l1_fee_scalar': transaction["receipt_l1_fee_scalar"],
            'receipt_l1_gas_used': transaction["receipt_l1_gas_used"],
            'receipt_l1_gas_price': transaction["receipt_l1_gas_price"],
            'blob_versioned_hashes': [bytes(_, 'utf-8') for _ in transaction["blob_versioned_hashes"]] \
                if transaction["blob_versioned_hashes"] else None,
            'receipt_contract_address': bytes(transaction["receipt_contract_address"],
                                              'utf-8') if transaction["receipt_contract_address"] else None,
            'exist_error': transaction["exist_error"],
            'error': transaction["error"],
            'revert_reason': transaction["revert_reason"],
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_log(self, log):
        return {
            'log_index': log["log_index"],
            'address': bytes(log["address"], 'utf-8'),
            'data': bytes(log["data"], 'utf-8'),
            'topic0': bytes(log["topic0"], 'utf-8'),
            'topic1': bytes(log["topic1"], 'utf-8') if log["topic1"] else None,
            'topic2': bytes(log["topic2"], 'utf-8') if log["topic2"] else None,
            'topic3': bytes(log["topic3"], 'utf-8') if log["topic3"] else None,
            'transaction_hash': bytes(log["transaction_hash"], 'utf-8'),
            'transaction_index': log["transaction_index"],
            'block_number': log["block_number"],
            'block_hash': bytes(log["block_hash"], 'utf-8'),
            'block_timestamp': func.to_timestamp(log["block_timestamp"]),
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_trace(self, trace):
        return {
            "trace_id": trace["trace_id"],
            "from_address": bytes(trace["from_address"], 'utf-8') if trace["from_address"] else None,
            "to_address": bytes(trace["to_address"], 'utf-8') if trace["to_address"] else None,
            "value": trace["value"],
            "input": bytes(trace["input"], 'utf-8') if trace["input"] else None,
            "output": bytes(trace["output"], 'utf-8') if trace["output"] else None,
            "trace_type": trace["trace_type"],
            "call_type": trace["call_type"],
            "gas": trace["gas"],
            "gas_used": trace["gas_used"],
            "subtraces": trace["subtraces"],
            "trace_address": trace["trace_address"],
            "error": trace["error"],
            "status": trace["status"],
            'block_number': trace["block_number"],
            'block_hash': bytes(trace["block_hash"], 'utf-8') if trace["block_hash"] else None,
            'block_timestamp': func.to_timestamp(trace["block_timestamp"]),
            'transaction_index': trace["transaction_index"],
            'transaction_hash': bytes(trace["transaction_hash"], 'utf-8') if trace["transaction_hash"] else None,
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_coin_balance(self, coin_balance):
        return {
            'address': bytes(coin_balance['address'], 'utf-8'),
            'balance': coin_balance['balance'],
            'block_number': coin_balance["block_number"],
            'block_timestamp': func.to_timestamp(coin_balance["block_timestamp"]),
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_token_transfer(self, token_transfer):
        return {
            'transaction_hash': bytes(token_transfer["transaction_hash"], 'utf-8'),
            'log_index': token_transfer["log_index"],
            "from_address": bytes(token_transfer["from_address"], 'utf-8'),
            "to_address": bytes(token_transfer["to_address"], 'utf-8'),
            "amount": token_transfer["amount"],
            "token_id": token_transfer["token_id"],
            "token_type": token_transfer["token_type"],
            "token_address": bytes(token_transfer["token_address"], 'utf-8'),
            'block_number': token_transfer["block_number"],
            'block_hash': bytes(token_transfer["block_hash"], 'utf-8'),
            'block_timestamp': func.to_timestamp(token_transfer["block_timestamp"]),
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_token_balance(self, token_balance):
        return {
            'address': bytes(token_balance["address"], 'utf-8'),
            "token_id": token_balance["token_id"],
            "token_type": token_balance["token_type"],
            "token_address": bytes(token_balance["token_address"], 'utf-8'),
            "balance": token_balance["balance"],
            'block_number': token_balance["block_number"],
            'block_timestamp': func.to_timestamp(token_balance["block_timestamp"]),
            'update_time': func.to_timestamp(int(datetime.now(timezone.utc).timestamp())) if self.confirm else None,
        }

    def convert_to_block_ts_mapper(self, mapper):
        return {
            "ts": mapper["timestamp"],
            "block_number": mapper["block_number"],
            "timestamp": func.to_timestamp(mapper["timestamp"]),
        }
