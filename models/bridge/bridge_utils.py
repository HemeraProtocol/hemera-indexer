from typing import Optional, Tuple

import rlp
from models.types import Log
from rlp import Serializable
from rlp.sedes import big_endian_int, binary, boolean
from web3 import Web3 as w3


class OpBedrockDepositTx(Serializable):
    """
    Class to represent a Deposit Transaction with RLP encoding.
    """

    fields = [
        ("source_hash", binary),  # Uses binary format for hash
        ("from_address", binary),  # Address also in binary
        ("to_address", binary),  # Optional address in binary
        ("mint", big_endian_int),  # Big integer, default to 0 if None
        ("value", big_endian_int),  # Big integer, default to 0 if None
        ("gas", big_endian_int),  # Gas limit as big integer
        ("is_system_transaction", boolean),  # Boolean flag
        ("data", binary),  # Data as bytes
    ]

    def __init__(
            self,
            source_hash,
            from_address,
            to_address=None,
            mint=None,
            value=None,
            gas=0,
            is_system_transaction=False,
            data=b"",
    ):
        super().__init__(
            source_hash=source_hash,
            from_address=from_address,
            to_address=to_address,
            mint=mint,
            value=value,
            gas=gas,
            is_system_transaction=is_system_transaction,
            data=data,
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

    stripped_log_index = hex(event.log_index)[2:]
    from_stripped = event.topic1[26:]
    to_stripped = event.topic2[26:]

    prefixed_block_hash = stripped_block_hash.rjust(64, "0")
    prefixed_log_index = stripped_log_index.rjust(64, "0")
    deposit_id_hash = w3.keccak(hexstr=(f"{prefixed_block_hash}{prefixed_log_index}"))

    source_hash = w3.keccak(hexstr=("00".rjust(64, "0") + deposit_id_hash.hex()[2:]))

    opaque_content_offset = int(event.data[2:66], 16)
    opaque_content_length = int(event.data[66:130], 16)

    opaque_data = event.data[130 : 130 + opaque_content_length * 2]

    msg_value = int.from_bytes(bytes.fromhex(opaque_data[:64]), "big")
    value = int.from_bytes(bytes.fromhex(opaque_data[64:128]), "big")
    gas_limit = int.from_bytes(bytes.fromhex(opaque_data[128:144]), "big")
    is_creation = int.from_bytes(bytes.fromhex(opaque_data[144:146]), "big") != 0
    data = bytes.fromhex(opaque_data[146:])

    return OpBedrockDepositTx(
        source_hash=bytes.fromhex(source_hash.hex()[2:]),
        from_address=bytes.fromhex(from_stripped),
        to_address=bytes.fromhex(to_stripped),
        mint=msg_value,
        value=value,
        gas=gas_limit,
        is_system_transaction=is_creation,
        data=data,
    )


def get_version_and_index_from_nonce(nonce: int) -> (int, int):
    version = nonce >> 240
    index = nonce & int("0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", 16)
    return (version, index)


def unmarshal_deposit_version1(opaque_data: bytes) -> Tuple[Optional[int], int, int, int, int, bool, bytes]:
    assert len(opaque_data) >= 32 + 32 + 32 + 32 + 8 + 1, f"Unexpected opaqueData length: {len(opaque_data)}"
    offset = 0

    # uint256 mint
    mint = int.from_bytes(opaque_data[offset : offset + 32], "big")
    mint_option = None if mint == 0 else mint
    offset += 32

    # uint256 value
    value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint256 ethValue
    eth_value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint256 ethTxValue
    eth_tx_value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint64 gas
    gas = int.from_bytes(opaque_data[offset : offset + 8], "big")
    assert gas.bit_length() <= 64, "Bad gas value"
    offset += 8

    # uint8 isCreation
    is_creation = opaque_data[offset] == 1
    offset += 1

    # remaining bytes fill the data
    tx_data = opaque_data[offset:]

    return mint_option, value, eth_value, eth_tx_value, gas, is_creation, tx_data


def unmarshal_deposit_version0(opaque_data: bytes) -> Tuple[Optional[int], int, int, bool, bytes]:
    assert len(opaque_data) >= 32 + 32 + 8 + 1, f"Unexpected opaqueData length: {len(opaque_data)}"
    offset = 0

    # uint256 mint
    mint = int.from_bytes(opaque_data[offset : offset + 32], "big")
    mint_option = None if mint == 0 else mint
    offset += 32

    # uint256 value
    value = int.from_bytes(opaque_data[offset : offset + 32], "big")
    offset += 32

    # uint64 gas
    gas = int.from_bytes(opaque_data[offset : offset + 8], "big")
    assert gas.bit_length() <= 64, "Bad gas value"
    offset += 8

    # uint8 isCreation
    is_creation = opaque_data[offset] == 1
    offset += 1

    # transaction data
    tx_data = opaque_data[offset:]

    return mint_option, value, gas, is_creation, tx_data
