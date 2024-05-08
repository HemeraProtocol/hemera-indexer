from utils.utils import hex_to_dec, to_normalized_address


class EthLog(object):
    def __init__(self):
        self.log_index = None
        self.address = None
        self.data = None
        self.topic0 = None
        self.topic1 = None
        self.topic2 = None
        self.topic3 = None
        self.transaction_hash = None
        self.transaction_index = None
        self.block_number = None
        self.block_hash = None
        self.block_timestamp = None


def transfer_dict_to_log(log_dict):
    log = EthLog()
    log.log_index = hex_to_dec(log_dict['logIndex'])
    log.address = to_normalized_address(log_dict['address'])
    log.data = log_dict['data']
    log.topic0 = log_dict['topics'][0]
    log.topic1 = log_dict['topics'][1] if len(log_dict['topics']) > 1 else None
    log.topic2 = log_dict['topics'][2] if len(log_dict['topics']) > 2 else None
    log.topic3 = log_dict['topics'][3] if len(log_dict['topics']) > 3 else None
    log.transaction_hash = log_dict['transactionHash']
    log.transaction_index = hex_to_dec(log_dict['transactionIndex'])
    log.block_number = hex_to_dec(log_dict['blockNumber'])
    log.block_hash = log_dict['blockHash']
    log.block_timestamp = hex_to_dec(log_dict['blockTimestamp'])

    return log
