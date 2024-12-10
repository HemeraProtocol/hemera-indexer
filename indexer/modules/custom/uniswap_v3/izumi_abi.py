from common.utils.abi_code_utils import Event, Function

POSITIONS_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "liquidities",
        "outputs": [
            {"internalType": "int24", "name": "leftPt", "type": "int24"},
            {"internalType": "int24", "name": "rightPt", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "lastFeeScaleX_128", "type": "uint256"},
            {"internalType": "uint256", "name": "lastFeeScaleY_128", "type": "uint256"},
            {"internalType": "uint256", "name": "remainTokenX", "type": "uint256"},
            {"internalType": "uint256", "name": "remainTokenY", "type": "uint256"},
            {"internalType": "uint128", "name": "poolId", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_POOL_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "tokenX", "type": "address"},
            {"internalType": "address", "name": "tokenY", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "name": "pool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_POOL_METAS_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "name": "poolMetas",
        "outputs": [
            {"internalType": "address", "name": "tokenX", "type": "address"},
            {"internalType": "address", "name": "tokenY", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_POOL_ID_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "poolIds",
        "outputs": [{"internalType": "uint128", "name": "poolId", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    }
)
SLOT0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "state",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPrice_96", "type": "uint160"},
            {"internalType": "int24", "name": "currentPoint", "type": "int24"},
            {"internalType": "uint16", "name": "observationCurrentIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationQueueLen", "type": "uint16"},
            {"internalType": "uint16", "name": "observationNextQueueLen", "type": "uint16"},
            {"internalType": "bool", "name": "locked", "type": "bool"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint128", "name": "liquidityX", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
POOL_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "tokenX", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "tokenY", "type": "address"},
            {"indexed": True, "internalType": "uint24", "name": "fee", "type": "uint24"},
            {"indexed": False, "internalType": "uint24", "name": "pointDelta", "type": "uint24"},
            {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
        ],
        "name": "NewPool",
        "type": "event",
    }
)
SWAP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "tokenX", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "tokenY", "type": "address"},
            {"indexed": True, "internalType": "uint24", "name": "fee", "type": "uint24"},
            {"indexed": False, "internalType": "bool", "name": "sellXEarnY", "type": "bool"},
            {"indexed": False, "internalType": "uint256", "name": "amountX", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountY", "type": "uint256"},
            {"indexed": False, "internalType": "int24", "name": "currentPoint", "type": "int24"},
        ],
        "name": "Swap",
        "type": "event",
    }
)
OWNER_OF_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
FACTORY_FUNCTION = Function(
    {
        "inputs": [],
        "name": "factory",
        "outputs": [{"internalType": "address", "name": "factory", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
FEE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "fee", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    }
)
TOKEN0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "tokenX",
        "outputs": [{"internalType": "address", "name": "tokenX", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
TOKEN1_FUNCTION = Function(
    {
        "inputs": [],
        "name": "tokenY",
        "outputs": [{"internalType": "address", "name": "tokenY", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
POINT_DELTA_FUNCTION = Function(
    {
        "inputs": [],
        "name": "pointDelta",
        "outputs": [{"internalType": "int24", "name": "pointDelta", "type": "int24"}],
        "stateMutability": "view",
        "type": "function",
    }
)
INCREASE_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "nftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "uint128", "name": "liquidityDelta", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amountX", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountY", "type": "uint256"},
        ],
        "name": "AddLiquidity",
        "type": "event",
    }
)
BURN_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "int24", "name": "leftPoint", "type": "int24"},
            {"indexed": True, "internalType": "int24", "name": "rightPoint", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amountX", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountY", "type": "uint256"},
        ],
        "name": "Burn",
        "type": "event",
    }
)
UPDATE_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "arg2", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "int128", "name": "arg4", "type": "int128"},
            {"indexed": False, "internalType": "int24", "name": "arg5", "type": "int24"},
            {"indexed": False, "internalType": "int24", "name": "arg6", "type": "int24"},
        ],
        "name": "UpdateLiquidity",
        "type": "event",
    }
)
DECREASE_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "nftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "uint128", "name": "liquidityDelta", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amountX", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountY", "type": "uint256"},
        ],
        "name": "DecLiquidity",
        "type": "event",
    }
)
MINT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "int24", "name": "leftPoint", "type": "int24"},
            {"indexed": True, "internalType": "int24", "name": "rightPoint", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amountX", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountY", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    }
)
