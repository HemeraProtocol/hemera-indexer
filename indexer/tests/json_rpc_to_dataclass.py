import json
from typing import Optional

from eth_utils import to_int

from indexer.domains.log import Log
from indexer.domains.receipt import Receipt
from indexer.domains.transaction import Transaction
from indexer.utils.json_rpc_requests import generate_get_block_by_number_json_rpc, generate_get_receipt_json_rpc
from indexer.utils.provider import BatchHTTPProvider
from indexer.utils.rpc_utils import rpc_response_batch_to_results


def get_transaction_from_rpc(rpc: str, transaction_hash: str) -> Optional[Transaction]:
    provider = BatchHTTPProvider(rpc)
    response = provider.make_request(params=json.dumps(list(generate_get_receipt_json_rpc([transaction_hash]))))
    results = list(rpc_response_batch_to_results(response))

    if not results:
        return None

    transaction_receipt = results[0]

    block_number = to_int(hexstr=transaction_receipt["blockNumber"])
    response = provider.make_request(
        params=json.dumps(list(generate_get_block_by_number_json_rpc([block_number], True)))
    )
    results = list(rpc_response_batch_to_results(response))
    block = results[0]
    block_timestamp = to_int(hexstr=block["timestamp"])
    block_hash = block["hash"]
    filtered_transactions = [
        transaction for transaction in block["transactions"] if transaction["hash"] == transaction_hash
    ]
    transaction_info = filtered_transactions[0] if filtered_transactions else None
    transaction_index = to_int(hexstr=transaction_info["transactionIndex"])
    if not block or not transaction_info:
        return None
    receipt = Receipt(
        transaction_hash=transaction_hash,
        transaction_index=transaction_index,
        status=to_int(hexstr=transaction_receipt["status"]),
        gas_used=to_int(hexstr=transaction_receipt["gasUsed"]),
        contract_address=transaction_receipt.get("contractAddress"),
        logs=[],
    )

    for log in transaction_receipt["logs"]:
        topics = log["topics"]
        receipt.logs.append(
            Log(
                log_index=to_int(hexstr=log["logIndex"]),
                address=log["address"],
                data=log["data"],
                transaction_hash=transaction_hash,
                transaction_index=transaction_index,
                block_timestamp=block_timestamp,
                block_number=block_number,
                block_hash=block_hash,
                topic0=topics[0] if len(topics) > 0 else None,
                topic1=topics[1] if len(topics) > 1 else None,
                topic2=topics[2] if len(topics) > 2 else None,
                topic3=topics[3] if len(topics) > 3 else None,
            )
        )

    return Transaction(
        hash=transaction_hash,
        nonce=to_int(hexstr=transaction_info["nonce"]),
        transaction_index=transaction_index,
        from_address=transaction_info["from"],
        to_address=transaction_info["to"],
        value=to_int(hexstr=transaction_info["value"]),
        gas_price=to_int(hexstr=transaction_info["gasPrice"]),
        gas=to_int(hexstr=transaction_info["gas"]),
        transaction_type=to_int(hexstr=transaction_info["type"]),
        input=transaction_info["input"],
        block_number=block_number,
        block_timestamp=block_timestamp,
        block_hash=block_hash,
        receipt=receipt,
    )
