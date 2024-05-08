import itertools
import warnings


def hex_to_dec(hex_string):
    if hex_string is None:
        return None
    try:
        return int(hex_string, 16)
    except ValueError:
        print("Not a hex string %s" % hex_string)
        return hex_string


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


def to_normalized_address(address):
    if address is None or not isinstance(address, str):
        return address
    return address.lower()


def validate_range(range_start_incl, range_end_incl):
    if range_start_incl < 0 or range_end_incl < 0:
        raise ValueError('range_start and range_end must be greater or equal to 0')

    if range_end_incl < range_start_incl:
        raise ValueError('range_end must be greater or equal to range_start')


def rpc_response_batch_to_results(response):
    for response_item in response:
        yield rpc_response_to_result(response_item)


def rpc_response_to_result(response):
    result = response.get('result')
    if result is None:
        error_message = 'result is None in response {}.'.format(response)
        if response.get('error') is None:
            error_message = error_message + ' Make sure Ethereum node is synced.'
            # When nodes are behind a load balancer it makes sense to retry the request in hopes it will go to other,
            # synced node
            raise ValueError(error_message)
        elif response.get('error') is not None and is_retriable_error(response.get('error').get('code')):
            raise ValueError(error_message)
        raise ValueError(error_message)
    return result


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


def trace_is_contract_creation(trace):
    return trace['trace_type'] == 'create' or trace['trace_type'] == 'create2'


def trace_is_transfer_value(trace):
    return trace['value'] is not None and trace['value'] > 0 and \
        trace['from_address'] != trace['to_address'] and trace['trace_type'] != 'delegatecall'
