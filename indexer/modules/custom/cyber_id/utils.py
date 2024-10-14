from ens.auto import ns
from ens.constants import EMPTY_SHA3_BYTES
from ens.utils import Web3, address_to_reverse_domain, is_empty_name, normal_name_to_hash, normalize_name
from hexbytes import HexBytes


def get_reverse_node(address):
    address = address_to_reverse_domain(address)
    return ns.namehash(address)


def label_to_hash(label: str) -> HexBytes:
    if "." in label:
        raise ValueError(f"Cannot generate hash for label {label!r} with a '.'")
    return Web3().keccak(text=label)


def get_node(name):
    node = EMPTY_SHA3_BYTES
    if not is_empty_name(name):
        labels = name.split(".")
        for label in reversed(labels):
            label_hash = label_to_hash(label)
            assert isinstance(label_hash, bytes)
            assert isinstance(node, bytes)
            node = Web3().keccak(node + label_hash)
    return node.hex()
