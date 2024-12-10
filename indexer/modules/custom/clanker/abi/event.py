from common.utils.abi_code_utils import Event

token_created_event_v1 = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "tokenAddress", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "lpNftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "deployer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "fid", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "supply", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "lockerAddress", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "castHash", "type": "string"},
        ],
        "name": "TokenCreated",
        "type": "event",
    }
)

token_created_event_v0 = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "tokenAddress", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "lpNftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "deployer", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "supply", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_supply", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "lockerAddress", "type": "address"},
        ],
        "name": "TokenCreated",
        "type": "event",
    }
)
