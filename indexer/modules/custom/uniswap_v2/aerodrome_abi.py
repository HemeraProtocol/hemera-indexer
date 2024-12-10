from common.utils.abi_code_utils import Event

POOL_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
            {"indexed": True, "internalType": "bool", "name": "stable", "type": "bool"},
            {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "PoolCreated",
        "type": "event",
    }
)

SWAP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount0In", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1In", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1Out", "type": "uint256"},
        ],
        "name": "Swap",
        "type": "event",
    }
)
