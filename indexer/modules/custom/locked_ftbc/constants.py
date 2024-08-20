MINT_LOCKED_FBTC_REQUEST_TOPIC0 = "0xe2666065de7c441f735695f729dbd8cd73297f1f974bb23784eb435183bedf83"

MINT_LOCKED_FBTC_REQUEST_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "address", "name": "minter", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "receivedAmount", "type": "uint256"},
        {"indexed": False, "internalType": "uint256", "name": "fee", "type": "uint256"},
    ],
    "name": "MintLockedFbtcRequest",
    "type": "event",
}
