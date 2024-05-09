from utils.utils import hex_to_dec, to_normalized_address


class EthBlock(object):
    def __init__(self):
        self.number = None
        self.timestamp = None
        self.hash = None
        self.parent_hash = None
        self.nonce = None

        self.gas_limit = None
        self.gas_used = None
        self.base_fee_per_gas = 0

        self.difficulty = None
        self.total_difficulty = None
        self.size = None
        self.miner = None
        self.sha3_uncles = None
        self.transactions_root = None
        self.transactions_count = 0

        self.state_root = None
        self.receipts_root = None
        self.extra_data = None
        self.withdrawals_root = None

    def __str__(self):
        return "EthBlock: " + vars(self).__str__()


def transfer_dict_to_block(block_dict):
    block = EthBlock()

    block.number = hex_to_dec(block_dict['number'])
    block.timestamp = hex_to_dec(block_dict['timestamp'])
    block.hash = block_dict['hash']
    block.parent_hash = block_dict['parentHash']
    block.nonce = block_dict['nonce']
    block.gas_limit = hex_to_dec(block_dict['gasLimit'])
    block.gas_used = hex_to_dec(block_dict['gasUsed'])
    block.base_fee_per_gas = hex_to_dec(block_dict['baseFeePerGas'])
    block.difficulty = hex_to_dec(block_dict['difficulty'])
    block.total_difficulty = hex_to_dec(block_dict['totalDifficulty'])
    block.size = hex_to_dec(block_dict['size'])
    block.miner = to_normalized_address(block_dict['miner'])
    block.sha3_uncles = block_dict['sha3Uncles']
    block.transactions_root = block_dict['transactionsRoot']
    block.transactions_count = len(block_dict['transactions'])
    block.state_root = block_dict['stateRoot']
    block.receipts_root = block_dict['receiptsRoot']
    block.extra_data = block_dict['extraData']
    block.withdrawals_root = block_dict['withdrawalsRoot']

    return block
