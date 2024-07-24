import itertools
import warnings
import random
from typing import List, Union

from indexer.domain import Domain

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TRANSFER_SINGLE_EVENT_TOPIC = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
TRANSFER_BATCH_EVENT_TOPIC = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
DEPOSIT_EVENT_TOPIC = "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
WITHDRAW_EVENT_TOPIC = "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"


def to_int_or_none(val):
    if isinstance(val, int):
        return val
    if val is None or val == '':
        return None
    try:
        return int(val)
    except ValueError:
        return None


def to_float_or_none(val):
    if isinstance(val, float):
        return val
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        print("can't cast %s to float" % val)
        return val


def chunk_string(string, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


# TODO: Implement fallback mechanism for provider uris instead of picking randomly
def pick_random_provider_uri(provider_uri):
    provider_uris = [uri.strip() for uri in provider_uri.split(',')]
    return random.choice(provider_uris)


def validate_range(range_start_incl, range_end_incl):
    if range_start_incl < 0 or range_end_incl < 0:
        raise ValueError('range_start and range_end must be greater or equal to 0')

    if range_end_incl < range_start_incl:
        raise ValueError('range_end must be greater or equal to range_start')


def rpc_response_batch_to_results(response):
    for response_item in response:
        yield rpc_response_to_result(response_item)


def rpc_response_to_result(response, ignore_errors=False):
    result = response.get('result')
    if result is None:
        error_message = 'result is None in response {}.'.format(response)
        if response.get('error') is None:
            error_message = error_message + ' Make sure Ethereum node is synced.'
            # When nodes are behind a load balancer it makes sense to retry the request in hopes it will go to other,
            # synced node
            raise ValueError(error_message)
        elif response.get('error') is not None and \
                is_retriable_error(response.get('error').get('code') and not ignore_errors):
            raise ValueError(error_message)
        elif not ignore_errors:
            raise ValueError(error_message)
        else:
            return result
    return result


def zip_rpc_response(requests, responses, index='request_id'):
    response_dict = {}
    for response in responses:
        response_dict[response['id']] = response

    for request in requests:
        request_id = request[index]
        if request_id in response_dict:
            yield request, response_dict[request_id]


def is_retriable_error(error_code):
    if error_code is None:
        return False

    if not isinstance(error_code, int):
        return False

    # https://www.jsonrpc.org/specification#error_object
    if error_code == -32603 or (-32000 >= error_code >= -32099):
        return True

    return False


def split_to_batches(start_incl, end_incl, batch_size):
    """start_incl and end_incl are inclusive, the returned batch ranges are also inclusive"""
    for batch_start in range(start_incl, end_incl + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_incl)
        yield batch_start, batch_end


def dynamic_batch_iterator(iterable, batch_size_getter):
    batch = []
    batch_size = batch_size_getter()
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
            batch_size = batch_size_getter()
    if len(batch) > 0:
        yield batch


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def check_classic_provider_uri(chain, provider_uri):
    if chain == 'classic' and provider_uri == 'https://mainnet.infura.io':
        warnings.warn("ETC Chain not supported on Infura.io. Using https://ethereumclassic.network instead")
        return 'https://ethereumclassic.network'
    return provider_uri


def verify_db_connection_url(db_url):
    if not db_url.startswith("postgresql"):
        raise ValueError("db_url must start with 'postgresql'")
    return db_url


def merge_sort(sorted_col_a, sorted_col_b):
    merged = []
    a_index, a_len = 0, len(sorted_col_a)
    b_index, b_len = 0, len(sorted_col_b)

    while a_index < a_len and b_index < b_len:
        if sorted_col_a[a_index]["id"] < sorted_col_b[b_index]["id"]:
            merged.append(sorted_col_a[a_index])
            a_index += 1
        else:
            merged.append(sorted_col_b[b_index])
            b_index += 1

    merged.extend(sorted_col_a[a_index:])
    merged.extend(sorted_col_b[b_index:])

    return merged


def distinct_collections_by_group(collections: List[Domain],
                                  group_by: List[str],
                                  max_key: Union[str, None] = None):
    distinct = {}
    for item in collections:
        key = tuple(getattr(item, idx) for idx in group_by)

        if key not in distinct:
            distinct[key] = item
        else:
            if max_key is not None and getattr(distinct[key], max_key) < getattr(item, max_key):
                distinct[key] = item

    return [distinct[key] for key in distinct.keys()]
