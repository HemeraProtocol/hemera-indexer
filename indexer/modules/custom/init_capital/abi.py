from common.utils.abi_code_utils import Event, Function

INIT_BORROW_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "borrowAmt", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
        ],
        "name": "Borrow",
        "type": "event",
    }
)


INIT_COLLATERALIZE_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amt", "type": "uint256"},
        ],
        "name": "Collateralize",
        "type": "event",
    }
)


INIT_COLLATERALIZE_WLP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "wLp", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amt", "type": "uint256"},
        ],
        "name": "CollateralizeWLp",
        "type": "event",
    }
)


INIT_CREATE_POSITION_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": False, "internalType": "uint16", "name": "mode", "type": "uint16"},
            {"indexed": False, "internalType": "address", "name": "viewer", "type": "address"},
        ],
        "name": "CreatePosition",
        "type": "event",
    }
)


INIT_DECOLLATERALIZE_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amt", "type": "uint256"},
        ],
        "name": "Decollateralize",
        "type": "event",
    }
)


INIT_DECOLLATERALIZE_WLP_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "wLp", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amt", "type": "uint256"},
        ],
        "name": "Decollateralize",
        "type": "event",
    }
)

INIT_LIQUIDATE_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "liquidator", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "poolOut", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
        ],
        "name": "Liquidate",
        "type": "event",
    }
)

INIT_LIQUIDATE_WLP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "liquidator", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "wLpOut", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amt", "type": "uint256"},
        ],
        "name": "LiquidateWLp",
        "type": "event",
    }
)

INIT_REPAY_EVENT = Event(
    {
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "posId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "repayer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amtToRepay", "type": "uint256"},
        ],
        "name": "Repay",
        "type": "event",
    }
)


INIT_SWAP_TO_REDUCE_POS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "initPosId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "tokenIn", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "tokenOut", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amtIn", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amtOut", "type": "uint256"},
        ],
        "name": "SwapToReducePos",
        "type": "event",
    }
)


INIT_SWAP_TO_INCREASE_POS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "initPosId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "tokenIn", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "tokenOut", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amtIn", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amtOut", "type": "uint256"},
        ],
        "name": "SwapToIncreasePos",
        "type": "event",
    }
)

INIT_INCREASE_POS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "initPosId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "tokenIn", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "borrToken", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amtIn", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "borrowAmt", "type": "uint256"},
        ],
        "name": "IncreasePos",
        "type": "event",
    },
)

INIT_REDUCE_POS_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "initPosId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "tokenOut", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amtOut", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "size", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "repayAmt", "type": "uint256"},
        ],
        "name": "ReducePos",
        "type": "event",
    }
)


INIT_POOL_TOTAL_SUPPLY_FUNCTION = Function(
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

INIT_POOL_TOTAL_DEBT_SHARES_FUNCTION = Function(
    {
        "inputs": [],
        "name": "totalDebtShares",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)


INIT_POOL_TOTAL_DEBT_FUNCTION = Function(
    {
        "inputs": [],
        "name": "totalDebt",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)


INIT_POOL_TOTAL_ASSETS_FUNCTION = Function(
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
