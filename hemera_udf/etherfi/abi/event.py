from hemera.common.utils.abi_code_utils import Event

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

validator_approved_event = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "validatorId", "type": "uint256"}],
        "name": "ValidatorApproved",
        "type": "event",
    }
)

rebase_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "totalEthLocked", "type": "uint256"},
            {"indexed": False, "name": "totalEEthShares", "type": "uint256"},
        ],
        "name": "Rebase",
        "type": "event",
    }
)

validator_registration_canceled_event = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "validatorId", "type": "uint256"}],
        "name": "ValidatorRegistrationCanceled",
        "type": "event",
    }
)

exchange_rate_changed_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "uint96", "name": "oldRate", "type": "uint96"},
            {"indexed": False, "internalType": "uint96", "name": "newRate", "type": "uint96"},
            {"indexed": False, "internalType": "uint64", "name": "currentTime", "type": "uint64"},
        ],
        "name": "ExchangeRateUpdated",
        "type": "event",
    }
)
