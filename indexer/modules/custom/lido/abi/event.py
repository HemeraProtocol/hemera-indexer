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

shares_burnt_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "account", "type": "address"},
            {"indexed": False, "name": "preRebaseTokenAmount", "type": "uint256"},
            {"indexed": False, "name": "postRebaseTokenAmount", "type": "uint256"}, 
            {"indexed": False, "name": "sharesAmount", "type": "uint256"}
        ],
        "name": "SharesBurnt",
        "type": "event"
    }
)

submitted_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "referral", "type": "address"}
        ],
        "name": "Submitted",
        "type": "event"
    }
)

el_rewards_received_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "ELRewardsReceived", 
        "type": "event"
    }
)

withdrawals_received_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "WithdrawalsReceived",
        "type": "event"
    }
)

unbuffered_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "amount", "type": "uint256"}
        ],
        "name": "Unbuffered",
        "type": "event"
    }
)

eth_distributed_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reportTimestamp", "type": "uint256"},
            {"indexed": False, "name": "preCLBalance", "type": "uint256"},
            {"indexed": False, "name": "postCLBalance", "type": "uint256"},
            {"indexed": False, "name": "withdrawalsWithdrawn", "type": "uint256"},
            {"indexed": False, "name": "executionLayerRewardsWithdrawn", "type": "uint256"},
            {"indexed": False, "name": "postBufferedEther", "type": "uint256"}
        ],
        "name": "ETHDistributed",
        "type": "event"
    }
)

cl_validators_updated_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reportTimestamp", "type": "uint256"},
            {"indexed": False, "name": "preCLValidators", "type": "uint256"},
            {"indexed": False, "name": "postCLValidators", "type": "uint256"}
        ],
        "name": "CLValidatorsUpdated",
        "type": "event"
    }
)

deposited_validators_changed_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "depositedValidators", "type": "uint256"}
        ],
        "name": "DepositedValidatorsChanged",
        "type": "event"
    }
)

