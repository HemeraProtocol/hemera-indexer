#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/12 下午2:10
Author  : xuzh
Project : hemera_indexer
"""
from common.utils.abi_code_utils import Event, Function

# log event
WETH_DEPOSIT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "dst", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

WETH_WITHDRAW_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "src", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Withdrawal",
        "type": "event",
    }
)

ERC20_TRANSFER_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
)

ERC721_TRANSFER_EVENT = ERC20_TRANSFER_EVENT

ERC1155_SINGLE_TRANSFER_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "id", "type": "uint256"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "TransferSingle",
        "type": "event",
    }
)

ERC1155_BATCH_TRANSFER_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "ids", "type": "uint256[]"},
            {"indexed": False, "name": "values", "type": "uint256[]"},
        ],
        "name": "TransferBatch",
        "type": "event",
    }
)

# ABI function
TOKEN_NAME_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN_SYMBOL_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN_DECIMALS_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN_TOTAL_SUPPLY_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "totalSupply", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN_TOTAL_SUPPLY_WITH_ID_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [{"name": "id", "type": "uint256"}],
        "name": "totalSupply",
        "outputs": [{"name": "totalSupply", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

ERC721_OWNER_OF_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"name": "owner", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

ERC721_TOKEN_URI_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "uri", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

ERC1155_MULTIPLE_TOKEN_URI_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "uri",
        "outputs": [{"name": "uri", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

ERC20_BALANCE_OF_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

ERC1155_TOKEN_ID_BALANCE_OF_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "id", "type": "uint256"},
        ],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

SUBMIT_INDEX_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint256", "name": "chainId_", "type": "uint256"},
            {"internalType": "uint256", "name": "startBlock_", "type": "uint256"},
            {"internalType": "uint256", "name": "endBlock_", "type": "uint256"},
            {"internalType": "uint256", "name": "codeHash_", "type": "bytes32"},
            {
                "components": [
                    {"internalType": "bytes32", "name": "dataClass", "type": "bytes4"},
                    {"internalType": "uint256", "name": "count", "type": "uint256"},
                    {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
                ],
                "internalType": "struct HemeraHistoryTransparency.IndexerOutput[]",
                "name": "outputs_",
                "type": "tuple[]",
            },
        ],
        "name": "submitIndexRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

REGISTER_FEATURE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "bytes4[]", "name": "dataClass_", "type": "bytes4[]"},
            {"internalType": "bytes32[]", "name": "gitCommitHash_", "type": "bytes32[]"},
        ],
        "name": "registerFeature",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
