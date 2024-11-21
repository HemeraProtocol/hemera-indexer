from common.utils.abi_code_utils import Event

create_market_event_v3 = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "market", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "PT", "type": "address"},
            {"indexed": False, "internalType": "int256", "name": "scalarRoot", "type": "int256"},
            {"indexed": False, "internalType": "int256", "name": "initialAnchor", "type": "int256"},
            {"indexed": False, "internalType": "uint256", "name": "lnFeeRateRoot", "type": "uint256"},
        ],
        "name": "CreateNewMarket",
        "type": "event",
    }
)

create_market_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "market", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "PT", "type": "address"},
            {"indexed": False, "internalType": "int256", "name": "scalarRoot", "type": "int256"},
            {"indexed": False, "internalType": "int256", "name": "initialAnchor", "type": "int256"},
        ],
        "name": "CreateNewMarket",
        "type": "event",
    }
)
