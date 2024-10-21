#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/21 下午5:50
Author  : xuzh
Project : hemera_indexer
"""
from common.utils.abi_code_utils import Function

OP_PROTOCOL_DEPOSIT_ETH_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint32", "name": "_minGasLimit", "type": "uint32"},
            {"internalType": "bytes", "name": "_extraData", "type": "bytes"},
        ],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)

OP_PROTOCOL_BRIDGE_ETH_TO_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint32", "name": "_minGasLimit", "type": "uint32"},
            {"internalType": "bytes", "name": "_extraData", "type": "bytes"},
        ],
        "name": "bridgeETHTo",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)

OP_PROTOCOL_DEPOSIT_ERC20_TO_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "uint32", "name": "_minGasLimit", "type": "uint32"},
            {"internalType": "bytes", "name": "_extraData", "type": "bytes"},
        ],
        "name": "depositERC20To",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

ARBITRUM_OUTBOUND_TRANSFER_FUNCTION = Function(
    {
        "inputs": [
            {"name": "_l1Token", "type": "address", "internalType": "address"},
            {"name": "_to", "type": "address", "internalType": "address"},
            {"name": "_amount", "type": "uint256", "internalType": "uint256"},
            {"name": "_maxGas", "type": "uint256", "internalType": "uint256"},
            {"name": "_gasPriceBid", "type": "uint256", "internalType": "uint256"},
            {"name": "_data", "type": "bytes", "internalType": "bytes"},
        ],
        "name": "outboundTransfer",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

LINEA_PROTOCOL_SEND_MESSAGE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_fee", "type": "uint256"},
            {"internalType": "bytes", "name": "_calldata", "type": "bytes"},
        ],
        "name": "sendMessage",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)

LINEA_PROTOCOL_BRIDGE_TOKEN_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "address", "name": "_recipient", "type": "address"},
        ],
        "name": "bridgeToken",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)

LINEA_PROTOCOL_DEPOSIT_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "address", "name": "_to", "type": "address"},
        ],
        "name": "depositTo",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)

function_mapping = {
    "op_deposit_eth": OP_PROTOCOL_DEPOSIT_ETH_FUNCTION,
    "op_bridge_eth_to": OP_PROTOCOL_BRIDGE_ETH_TO_FUNCTION,
    "op_deposit_erc20_to": OP_PROTOCOL_DEPOSIT_ERC20_TO_FUNCTION,
    "arbitrum_outbound_transfer": ARBITRUM_OUTBOUND_TRANSFER_FUNCTION,
    "linea_send_message": LINEA_PROTOCOL_SEND_MESSAGE_FUNCTION,
    "linea_bridge_token": LINEA_PROTOCOL_BRIDGE_TOKEN_FUNCTION,
    "linea_deposit_to": LINEA_PROTOCOL_DEPOSIT_FUNCTION,
}
