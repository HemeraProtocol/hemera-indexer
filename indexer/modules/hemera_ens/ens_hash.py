#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/5/23 17:18
# @Author  will
# @File  ens_hash.py
# @Brief
from eth_utils import keccak
from web3 import Web3


def namehash(name):
    """
    Calculate the namehash of an ENS name.

    :param name: The ENS name to hash (e.g., 'example.eth').
    :return: The namehash as a hexadecimal string.
    """
    node = b"\x00" * 32
    if name:
        labels = name.split(".")
        for label in reversed(labels):
            node = keccak(node + keccak(label.encode("utf-8")))
    return Web3.to_hex(node)


def get_label(name):
    return Web3.to_hex(keccak(name.encode("utf-8")))


def compute_node_label(base_node, label):
    base_node = base_node.lower()
    if base_node.startswith("0x"):
        base_node = base_node[2:]
    label = label.lower()
    if label.startswith("0x"):
        label = label[2:]

    node = keccak(bytes.fromhex(base_node) + bytes.fromhex(label))
    return Web3.to_hex(node).lower()


if __name__ == "__main__":
    print(compute_node_label('93CDEB708B7545DC668EB9280176169D1C33CFD8ED6F04690A0BCC88A93FC4AE', "AF2CAA1C2CA1D027F1AC823B529D0A67CD144264B2789FA2EA4D63A67C7103CC"))