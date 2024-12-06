from common.utils.abi_code_utils import Event

PAIR_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "pair", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "PairCreated",
        "type": "event",
    }
)
