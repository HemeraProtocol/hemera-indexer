ABI_LIST = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint24", "name": "id", "type": "uint24"}],
        "name": "getBin",
        "outputs": [
            {"internalType": "uint128", "name": "binReserveX", "type": "uint128"},
            {"internalType": "uint128", "name": "binReserveY", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
