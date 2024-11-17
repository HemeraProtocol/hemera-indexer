from common.utils.abi_code_utils import Event, Function

MINT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "minter", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    }
)


TRANSFER_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
)

APPROVAL_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "spender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
        ],
        "name": "Approval",
        "type": "event",
    }
)

BURN_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "burner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "Burn",
        "type": "event",
    }
)

TOKENRSENT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "msgHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint64", "name": "canonicalChainId", "type": "uint64"},
            {"indexed": False, "internalType": "uint64", "name": "destChainId", "type": "uint64"},
            {"indexed": False, "internalType": "address", "name": "ctoken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "TokenSent",
        "type": "event",
    }
)

TOKENRECEIVED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "msgHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint64", "name": "srcChainId", "type": "uint64"},
            {"indexed": False, "internalType": "address", "name": "ctoken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "TokenReceived",
        "type": "event",
    }
)


MESSAGESENT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "msgHash", "type": "bytes32"},
            {"indexed": False, "internalType": "tuple", "name": "message", "type": "tuple"},   
        ],
        "name": "MessageSent",
        "type": "event",
    }
)


MESSAGESTATUSCHANGED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "msgHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint8", "name": "status", "type": "uint8"},
        ],
        "name": "MessageStatusChanged",
        "type": "event",
    }
)


MESSAGEPROCESSED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "msgHash", "type": "bytes32"},
            {"indexed": False, "internalType": "tuple", "name": "message", "type": "tuple"},
            {"indexed": False, "internalType": "tuple", "name": "stats", "type": "tuple"},    
        ],
        "name": "MessageProcessed",
        "type": "event",
    }
)

SIGNALSENT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "app", "type": "address"},
            {"indexed": False, "internalType": "bytes32", "name": "signal", "type": "bytes32"}, 
            {"indexed": False, "internalType": "bytes32", "name": "slot", "type": "bytes32"}, 
            {"indexed": False, "internalType": "bytes32", "name": "value", "type": "bytes32"},    
        ],
        "name": "SignalSent",
        "type": "event",
    }
)

# todo: other event

