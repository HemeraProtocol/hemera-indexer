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
]

TOKEN_ASSET_DICT = {
    "0x3880233e78966eb13a9c2881d5f162d646633178": {
        "getTokenX": "0xc96de26018a54d51c097160568752c4e3bd6c364",
        "getTokenY": "0xcda86a272531e8640cd7f1a92c01839911b90bb0",
    }
}
LIQUIDITY_LIST = [
    "0x87f1f9dcf5e8089a3e00811b6a008d8f30293a3da878cb1fe8c90ca376402f8a",
    "0xa32e146844d6144a22e94c586715a1317d58a8aa3581ec33d040113ddcb24350",
    "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb",
]
