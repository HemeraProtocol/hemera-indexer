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
    {
        "inputs": [],
        "name": "getTokenX",
        "outputs": [{"internalType": "address", "name": "tokenX", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getTokenY",
        "outputs": [{"internalType": "address", "name": "tokenY", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getActiveId",
        "outputs": [{"internalType": "uint24", "name": "activeId", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getBinStep",
        "outputs": [{"internalType": "uint24", "name": "binStep", "type": "uint16"}],
        "stateMutability": "view",
        "type": "function",
    },
]

LIQUIDITY_LIST = [
    # DepositedToBins
    "0x87f1f9dcf5e8089a3e00811b6a008d8f30293a3da878cb1fe8c90ca376402f8a",
    # WithdrawnFromBins
    "0xa32e146844d6144a22e94c586715a1317d58a8aa3581ec33d040113ddcb24350",
    # TransferBatch
    "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb",
]
