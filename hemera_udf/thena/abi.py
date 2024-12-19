from hemera.common.utils.abi_code_utils import Event, Function

MINT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "int24", "name": "bottomTick", "type": "int24"},
            {"indexed": True, "internalType": "int24", "name": "topTick", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidityAmount", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    }
)

BURN_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "int24", "name": "bottomTick", "type": "int24"},
            {"indexed": True, "internalType": "int24", "name": "topTick", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidityAmount", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "Burn",
        "type": "event",
    }
)
LIQUIDITY_FUNCTION = Function(
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    }
)

BALANCE_OF_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

TOTAL_SUPPLY_FUNCTION = Function(
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

BASE_LOWER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "baseLower",
        "outputs": [{"internalType": "int24", "name": "", "type": "int24"}],
        "stateMutability": "view",
        "type": "function",
    }
)
BASE_UPPER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "baseUpper",
        "outputs": [{"internalType": "int24", "name": "", "type": "int24"}],
        "stateMutability": "view",
        "type": "function",
    }
)
