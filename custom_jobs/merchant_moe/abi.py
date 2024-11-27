from common.utils.abi_code_utils import Event, Function

TOTAL_SUPPLY_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

GET_BIN_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint24", "name": "id", "type": "uint24"}],
        "name": "getBin",
        "outputs": [
            {"internalType": "uint128", "name": "binReserveX", "type": "uint128"},
            {"internalType": "uint128", "name": "binReserveY", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)

GET_TOKENX_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getTokenX",
        "outputs": [{"internalType": "address", "name": "tokenX", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

GET_TOKENY_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getTokenY",
        "outputs": [{"internalType": "address", "name": "tokenY", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

GET_ACTIVE_ID_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getActiveId",
        "outputs": [{"internalType": "uint24", "name": "activeId", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    }
)

GET_BIN_STEP_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getBinStep",
        "outputs": [{"internalType": "uint24", "name": "binStep", "type": "uint16"}],
        "stateMutability": "view",
        "type": "function",
    }
)

DEPOSITED_TO_BINS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
            {"indexed": False, "internalType": "bytes32[]", "name": "amounts", "type": "bytes32[]"},
        ],
        "name": "DepositedToBins",
        "type": "event",
    }
)

WITHDRAWN_FROM_BINS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
            {"indexed": False, "internalType": "bytes32[]", "name": "amounts", "type": "bytes32[]"},
        ],
        "name": "WithdrawnFromBins",
        "type": "event",
    }
)

TRANSFER_BATCH_EVNET = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
            {"indexed": False, "internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
        ],
        "name": "TransferBatch",
        "type": "event",
    }
)

SWAP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint24", "name": "id", "type": "uint24"},
            {"indexed": False, "internalType": "bytes32", "name": "amountsIn", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes32", "name": "amountsOut", "type": "bytes32"},
            {"indexed": False, "internalType": "uint24", "name": "volatilityAccumulator", "type": "uint24"},
            {"indexed": False, "internalType": "bytes32", "name": "totalFees", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes32", "name": "protocolFees", "type": "bytes32"},
        ],
        "name": "Swap",
        "type": "event",
    }
)

LB_PAIR_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "contract IERC20", "name": "tokenX", "type": "address"},
            {"indexed": True, "internalType": "contract IERC20", "name": "tokenY", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "binStep", "type": "uint256"},
            {"indexed": False, "internalType": "contract ILBPair", "name": "LBPair", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "pid", "type": "uint256"},
        ],
        "name": "LBPairCreated",
        "type": "event",
    }
)
