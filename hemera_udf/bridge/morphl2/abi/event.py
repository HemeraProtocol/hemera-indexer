from hemera.common.utils.abi_code_utils import Event

SentMessageEvent = Event(
    {
        "type": "event",
        "name": "SentMessage",
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "messageNonce", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "gasLimit", "type": "uint256"},
            {"indexed": False, "internalType": "bytes", "name": "message", "type": "bytes"},
        ],
        "anonymous": False,
    }
)

RelayedMessageEvent = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "internalType": "bytes32", "name": "messageHash", "type": "bytes32"}],
        "name": "RelayedMessage",
        "type": "event",
    }
)

QueueTransactionEvent = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"},
            {"indexed": False, "internalType": "uint64", "name": "queueIndex", "type": "uint64"},
            {"indexed": False, "internalType": "uint256", "name": "gasLimit", "type": "uint256"},
            {"indexed": False, "internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "QueueTransaction",
        "type": "event",
    }
)
