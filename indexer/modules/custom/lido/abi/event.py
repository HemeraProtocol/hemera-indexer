from common.utils.abi_code_utils import Event

transfer_share_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "sharesValue", "type": "uint256"},
        ],
        "name": "TransferShares",
        "type": "event",
    }
)
