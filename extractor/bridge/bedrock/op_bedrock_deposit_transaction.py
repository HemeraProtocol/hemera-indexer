import rlp
from rlp import Serializable
from rlp.sedes import binary, BigEndianInt, boolean, big_endian_int
from web3 import Web3 as w3

from extractor.types import Log


class OpBedrockDepositTx(Serializable):
    """
    Class to represent a Deposit Transaction with RLP encoding.
    """
    fields = [
        ('source_hash', binary),  # Uses binary format for hash
        ('from_address', binary),  # Address also in binary
        ('to_address', binary),  # Optional address in binary
        ('mint', big_endian_int),  # Big integer, default to 0 if None
        ('value', big_endian_int),  # Big integer, default to 0 if None
        ('gas', big_endian_int),  # Gas limit as big integer
        ('is_system_transaction', boolean),  # Boolean flag
        ('data', binary)  # Data as bytes
    ]

    def __init__(self, source_hash, from_address, to_address=None, mint=None, value=None, gas=0,
                 is_system_transaction=False, data=b''):
        super().__init__(
            source_hash=source_hash,
            from_address=from_address,
            to_address=to_address,
            mint=mint,
            value=value,
            gas=gas,
            is_system_transaction=is_system_transaction,
            data=data
        )

    def decode(self, encoded_tx):
        return rlp.decode(encoded_tx, sedes=OpBedrockDepositTx)

    def encode(self):
        return rlp.encode(self)

    def hash(self):
        encoded_tx = rlp.encode(self)
        return w3.keccak(hexstr="7e" + self.encode().hex()).hex()


def deposit_event_to_op_bedrock_transaction(event: Log):
    stripped_block_hash = event.block_hash[2:]
    transaction_hash = event.transaction_hash
    stripped_log_index = hex(event.log_index)[2:]
    from_stripped = event.topic1[26:]
    to_stripped = event.topic2[26:]

    prefixed_block_hash = stripped_block_hash.rjust(64, '0')
    prefixed_log_index = stripped_log_index.rjust(64, '0')
    print(f"{prefixed_block_hash}{prefixed_log_index}")
    deposit_id_hash = w3.keccak(hexstr = (f"{prefixed_block_hash}{prefixed_log_index}"))

    print('00'.rjust(64, '0') + deposit_id_hash.hex()[2:])
    source_hash = w3.keccak(hexstr = ('00'.rjust(64, '0') + deposit_id_hash.hex()[2:]))

    print("Source Hash: " + source_hash.hex())
    opaque_content_offset = int(event.data[2:66], 16)
    opaque_content_length = int(event.data[66:130], 16)

    opaque_data = event.data[130:130 + opaque_content_length * 2]

    msg_value = int.from_bytes(bytes.fromhex(opaque_data[:64]), 'big')
    value = int.from_bytes(bytes.fromhex(opaque_data[64:128]), 'big')
    gas_limit = int.from_bytes(bytes.fromhex(opaque_data[128:144]), 'big')
    is_creation = (int.from_bytes(bytes.fromhex(opaque_data[144:146]), 'big') != 0)
    data = bytes.fromhex(opaque_data[146:])

    return OpBedrockDepositTx(
        source_hash=bytes.fromhex(source_hash.hex()[2:]),
        from_address=bytes.fromhex(from_stripped),
        to_address=bytes.fromhex(to_stripped),
        mint=msg_value,
        value=value,
        gas=gas_limit,
        is_system_transaction=is_creation,
        data=data
    )