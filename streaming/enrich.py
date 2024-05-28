import itertools
from collections import defaultdict


def join(left, right, join_fields, left_fields, right_fields):
    left_join_field, right_join_field = join_fields

    def field_list_to_dict(field_list):
        result_dict = {}
        for field in field_list:
            if isinstance(field, tuple):
                result_dict[field[0]] = field[1]
            else:
                result_dict[field] = field
        return result_dict

    left_fields_as_dict = field_list_to_dict(left_fields)
    right_fields_as_dict = field_list_to_dict(right_fields)

    left_map = defaultdict(list)
    for item in left: left_map[item[left_join_field]].append(item)

    right_map = defaultdict(list)
    for item in right: right_map[item[right_join_field]].append(item)

    for key in left_map.keys():
        for left_item, right_item in itertools.product(left_map[key], right_map[key]):
            result_item = {}
            for src_field, dst_field in left_fields_as_dict.items():
                result_item[dst_field] = left_item.get(src_field)
            for src_field, dst_field in right_fields_as_dict.items():
                result_item[dst_field] = right_item.get(src_field)

            yield result_item


def enrich_transactions(transactions, receipts):
    result = list(join(
        transactions, receipts, ('hash', 'transactionHash'),
        left_fields=[
            'hash',
            'transactionIndex',
            'from',
            'to',
            'value',
            'type',
            'input',
            'nonce',
            'blockHash',
            'blockNumber',
            # 'block_timestamp',
            'gas',
            'gasPrice',
            'maxFeePerGas',
            'maxPriorityFeePerGas',
            'maxFeePerBlobGas',
            'blobVersionedHashes'
        ],
        right_fields=[
            ('gasUsed', 'receiptGasUsed'),
            ('cumulativeGasUsed', 'receiptCumulativeGasUsed'),
            ('effectiveGasPrice', 'receiptEffectiveGasPrice'),
            ('root', 'receiptRoot'),
            ('status', 'receiptStatus'),
            ('l1Fee', 'receiptL1Fee'),
            ('l1FeeScalar', 'receiptL1FeeScalar'),
            ('l1GasUsed', 'receiptL1GasUsed'),
            ('l1GasPrice', 'receiptL1GasPrice'),
            ('blobGasUsed', 'receiptBlobGasUsed'),
            ('blobGasPrice', 'receiptBlobGasPrice'),
            ('contractAddress', 'receiptContractAddress'),
            ('error', 'error'),
            ('revertReason', 'revertReason')
        ]))

    if len(result) != len(transactions):
        raise ValueError('The number of transactions is wrong ' + str(result))

    return result


def enrich_logs(blocks, logs):
    result = list(join(
        logs, blocks, ('block_number', 'number'),
        [
            'type',
            'log_index',
            'transaction_hash',
            'transaction_index',
            'address',
            'data',
            'topic0',
            'topic1',
            'topic2',
            'topic3',
            'block_number'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))

    if len(result) != len(logs):
        raise ValueError('The number of logs is wrong ' + str(result))

    return result


def enrich_token_transfers(blocks, token_transfers):
    result = list(join(
        token_transfers, blocks, ('block_number', 'number'),
        [
            'type',
            'token_address',
            'from_address',
            'to_address',
            'value',
            'transaction_hash',
            'log_index',
            'block_number'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))

    if len(result) != len(token_transfers):
        raise ValueError('The number of token transfers is wrong ' + str(result))

    return result


def enrich_traces(blocks, traces):
    result = list(join(
        traces, blocks, ('block_number', 'number'),
        [
            'type',
            'transaction_index',
            'from_address',
            'to_address',
            'value',
            'input',
            'output',
            'trace_type',
            'call_type',
            'reward_type',
            'gas',
            'gas_used',
            'subtraces',
            'trace_address',
            'error',
            'status',
            'transaction_hash',
            'block_number',
            'trace_id',
            'trace_index'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))

    if len(result) != len(traces):
        raise ValueError('The number of traces is wrong ' + str(result))

    return result


def enrich_geth_traces(blocks, traces):
    result = list(join(
        traces, blocks, ('block_number', 'number'),
        [
            'trace_id',
            'from_address',
            'to_address',
            'input',
            'output',
            'value',
            'gas',
            'gas_used',
            'trace_type',
            'call_type',
            'subtraces',
            'trace_address',
            'error',
            'status',
            'block_number',
            'transaction_index',
            'transaction_hash',
            'trace_index'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))


    if len(result) != len(traces):
        raise ValueError('The number of traces is wrong ' + str(result))

    return result


def enrich_contracts(blocks, contracts):
    result = list(join(
        contracts, blocks, ('block_number', 'number'),
        [
            'address',
            'contract_creator',
            'creation_code',
            'deployed_code',
            'block_number',
            'transaction_index',
            'transaction_hash',
            'name'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))

    if len(result) != len(contracts):
        raise ValueError('The number of contracts is wrong ' + str(result))

    return result


def enrich_tokens(blocks, tokens):
    result = list(join(
        tokens, blocks, ('block_number', 'number'),
        [
            'type',
            'address',
            'symbol',
            'name',
            'decimals',
            'total_supply',
            'block_number'
        ],
        [
            ('timestamp', 'block_timestamp'),
            ('hash', 'block_hash'),
        ]))

    if len(result) != len(tokens):
        raise ValueError('The number of tokens is wrong ' + str(result))

    return result


def enrich_blocks_timestamp(blocks, datas):
    block_timestamp = dict()
    for block in blocks:
        block_timestamp[block['number']] = block['timestamp']

    for data in datas:
        data['blockTimestamp'] = block_timestamp[data['blockNumber']]

    return datas
