from hemera.common.utils.abi_code_utils import Event, Function

# In v4, ADDRESS_ZERO is used to represent native ETH
ETH_ADDRESS = "0x0000000000000000000000000000000000000000"

POSITIONS_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)

CURRENCY_IS_NATIVE_FUNCTION = Function(
    {
        "inputs": [{"internalType": "Currency", "name": "currency", "type": "address"}],
        "name": "isNative",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    }
)

CURRENCY_WRAP_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "currency", "type": "address"}],
        "name": "wrap",
        "outputs": [{"internalType": "Currency", "name": "", "type": "address"}],
        "stateMutability": "pure",
        "type": "function",
    }
)

SETTLE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "settle",
        "outputs": [{"internalType": "uint256", "name": "paid", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
)

TAKE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "Currency", "name": "currency", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "take",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

UNLOCK_FUNCTION = Function(
    {
        "inputs": [{"internalType": "bytes", "name": "data", "type": "bytes"}],
        "name": "unlock",
        "outputs": [{"internalType": "bytes", "name": "", "type": "bytes"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

INITIALIZE_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "currency0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "currency1", "type": "address"},
            {"indexed": False, "internalType": "uint24", "name": "fee", "type": "uint24"},
            {"indexed": False, "internalType": "int24", "name": "tickSpacing", "type": "int24"},
            {"indexed": False, "internalType": "address", "name": "hooks", "type": "address"},
            {"indexed": False, "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": False, "internalType": "int24", "name": "tick", "type": "int24"},
        ],
        "name": "Initialize",
        "type": "event",
    }
)

CREATE_POOL_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "address[]", "name": "hooks", "type": "address[]"},
            {"internalType": "bytes[]", "name": "initData", "type": "bytes[]"},
        ],
        "name": "createPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)

GET_POOL_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint24", "name": "", "type": "uint24"},
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

SLOT0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)

POOL_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
            {"indexed": True, "internalType": "uint24", "name": "fee", "type": "uint24"},
            {"indexed": False, "internalType": "int24", "name": "tickSpacing", "type": "int24"},
            {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "address[]", "name": "hooks", "type": "address[]"},
        ],
        "name": "PoolCreated",
        "type": "event",
    }
)

SWAP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "int128", "name": "amount0", "type": "int128"},
            {"indexed": False, "internalType": "int128", "name": "amount1", "type": "int128"},
            {"indexed": False, "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "int24", "name": "tick", "type": "int24"},
            {"indexed": False, "internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "name": "Swap",
        "type": "event",
    }
)

MODIFY_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "int24", "name": "tickLower", "type": "int24"},
            {"indexed": False, "internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"indexed": False, "internalType": "int256", "name": "liquidityDelta", "type": "int256"},
            {"indexed": False, "internalType": "bytes32", "name": "salt", "type": "bytes32"},
        ],
        "name": "ModifyLiquidity",
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
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

FEE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

TOKEN1_FUNCTION = Function(
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

TICK_SPACING_FUNCTION = Function(
    {
        "inputs": [],
        "name": "tickSpacing",
        "outputs": [{"internalType": "int24", "name": "", "type": "int24"}],
        "stateMutability": "view",
        "type": "function",
    }
)

HOOKS_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getHooks",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

DONATE_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "Donate",
        "type": "event",
    }
)


BEFORE_INITIALIZE_SELECTOR = "0x60180975"
AFTER_INITIALIZE_SELECTOR = "0x58c0bbb5"
BEFORE_ADD_LIQUIDITY_SELECTOR = "0x826309f2"
AFTER_ADD_LIQUIDITY_SELECTOR = "0x32553a29"
BEFORE_REMOVE_LIQUIDITY_SELECTOR = "0xb58be774"
AFTER_REMOVE_LIQUIDITY_SELECTOR = "0x571b684a"
BEFORE_SWAP_SELECTOR = "0x00e91414"
AFTER_SWAP_SELECTOR = "0x59b0f6e5"
BEFORE_DONATE_SELECTOR = "0x7fec8241"
AFTER_DONATE_SELECTOR = "0x5896b6e8"


HOOK_CALLED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "hook", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "caller", "type": "address"},
            {"indexed": False, "internalType": "bytes4", "name": "selector", "type": "bytes4"},
            {"indexed": False, "internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "HookCalled",
        "type": "event",
    }
)
