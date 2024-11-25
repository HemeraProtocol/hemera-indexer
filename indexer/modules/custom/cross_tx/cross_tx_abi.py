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

TOKENSENT_EVENT = Event(
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
            {"components": [
          {
            "internalType": "uint64",
            "name": "id",
            "type": "uint64"
          },
          {
            "internalType": "uint64",
            "name": "fee",
            "type": "uint64"
          },
          {
            "internalType": "uint32",
            "name": "gasLimit",
            "type": "uint32"
          },
          {
            "internalType": "address",
            "name": "from",
            "type": "address"
          },
          {
            "internalType": "uint64",
            "name": "srcChainId",
            "type": "uint64"
          },
          {
            "internalType": "address",
            "name": "srcOwner",
            "type": "address"
          },
          {
            "internalType": "uint64",
            "name": "destChainId",
            "type": "uint64"
          },
          {
            "internalType": "address",
            "name": "destOwner",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "to",
            "type": "address"
          },
          {
            "internalType": "uint256",
            "name": "value",
            "type": "uint256"
          },
          {
            "internalType": "bytes",
            "name": "data",
            "type": "bytes"
          }
        ],
        "indexed": False,
        "internalType": "struct IBridge.Message",
        "name": "message",
        "type": "tuple"
      }
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
            {"indexed": False, "internalType": "enum IBridge.Status", "name": "status", "type": "uint8"},
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
            {"components": [{
                "internalType": "uint64",
                "name": "id",
                "type": "uint64"
            },
            {
                "internalType": "uint64",
                "name": "fee",
                "type": "uint64"
            },
            {
                "internalType": "uint32",
                "name": "gasLimit",
                "type": "uint32"
            },
            {
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "internalType": "uint64",
                "name": "srcChainId",
                "type": "uint64"
            },
            {
                "internalType": "address",
                "name": "srcOwner",
                "type": "address"
            },
            {
                "internalType": "uint64",
                "name": "destChainId",
                "type": "uint64"
            },
            {
                "internalType": "address",
                "name": "destOwner",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "to",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "value",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "data",
                "type": "bytes"
            }], "indexed": False, "internalType": "struct IBridge.Message", "name": "message", "type": "tuple"},
            {
                "components": [
                {
                    "internalType": "uint32",
                    "name": "gasUsedInFeeCalc",
                    "type": "uint32"
                },
                {
                    "internalType": "uint32",
                    "name": "proofSize",
                    "type": "uint32"
                },
                {
                    "internalType": "uint32",
                    "name": "numCacheOps",
                    "type": "uint32"
                },
                {
                    "internalType": "bool",
                    "name": "processedByRelayer",
                    "type": "bool"
                }],"indexed": False, "internalType": "struct Bridge.ProcessingStats","name": "stats","type": "tuple"}
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

