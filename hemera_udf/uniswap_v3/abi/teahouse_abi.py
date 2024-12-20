from hemera.common.utils.abi_code_utils import Event, Function

ADD_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "int24", "name": "tickLower", "type": "int24"},
            {"indexed": False, "internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "AddLiquidity",
        "type": "event",
    }
)
ADMIN_CHANGED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "previousAdmin", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "newAdmin", "type": "address"},
        ],
        "name": "AdminChanged",
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
BEACON_UPGRADED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "internalType": "address", "name": "beacon", "type": "address"}],
        "name": "BeaconUpgraded",
        "type": "event",
    }
)
COLLECT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "int24", "name": "tickLower", "type": "int24"},
            {"indexed": False, "internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "Collect",
        "type": "event",
    }
)
COLLECT_SWAP_FEES_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "feeAmount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "feeAmount1", "type": "uint256"},
        ],
        "name": "CollectSwapFees",
        "type": "event",
    }
)
DEPOSIT_SHARES_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "shareOwner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "feeAmount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "feeAmount1", "type": "uint256"},
        ],
        "name": "DepositShares",
        "type": "event",
    }
)
FEE_CONFIG_CHANGED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {
                "components": [
                    {"internalType": "address", "name": "vault", "type": "address"},
                    {"internalType": "uint24", "name": "entryFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "exitFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "performanceFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "managementFee", "type": "uint24"},
                ],
                "indexed": False,
                "internalType": "struct ITeaVaultV3Pair.FeeConfig",
                "name": "feeConfig",
                "type": "tuple",
            },
        ],
        "name": "FeeConfigChanged",
        "type": "event",
    }
)
INITIALIZED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": False, "internalType": "uint8", "name": "version", "type": "uint8"}],
        "name": "Initialized",
        "type": "event",
    }
)
MANAGEMENT_FEE_COLLECTED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}],
        "name": "ManagementFeeCollected",
        "type": "event",
    }
)
MANAGER_CHANGED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newManager", "type": "address"},
        ],
        "name": "ManagerChanged",
        "type": "event",
    }
)
OWNERSHIP_TRANSFERRED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousOwner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newOwner", "type": "address"},
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    }
)
REMOVE_LIQUIDITY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "pool", "type": "address"},
            {"indexed": False, "internalType": "int24", "name": "tickLower", "type": "int24"},
            {"indexed": False, "internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "RemoveLiquidity",
        "type": "event",
    }
)
SWAP_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bool", "name": "zeroForOne", "type": "bool"},
            {"indexed": True, "internalType": "bool", "name": "exactInput", "type": "bool"},
            {"indexed": False, "internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amountOut", "type": "uint256"},
        ],
        "name": "Swap",
        "type": "event",
    }
)
TEA_VAULT_V3_PAIR_CREATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "internalType": "address", "name": "teaVaultAddress", "type": "address"}],
        "name": "TeaVaultV3PairCreated",
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
UPGRADED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "internalType": "address", "name": "implementation", "type": "address"}],
        "name": "Upgraded",
        "type": "event",
    }
)
WITHDRAW_SHARES_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "shareOwner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "feeShares", "type": "uint256"},
        ],
        "name": "WithdrawShares",
        "type": "event",
    }
)
DECIMALS_MULTIPLIER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "DECIMALS_MULTIPLIER",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
FEE_CAP_FUNCTION = Function(
    {
        "inputs": [],
        "name": "FEE_CAP",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
FEE_MULTIPLIER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "FEE_MULTIPLIER",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
SECONDS_IN_A_YEAR_FUNCTION = Function(
    {
        "inputs": [],
        "name": "SECONDS_IN_A_YEAR",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
ADD_LIQUIDITY_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "_tickLower", "type": "int24"},
            {"internalType": "int24", "name": "_tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "_liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "_amount0Min", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount1Min", "type": "uint256"},
            {"internalType": "uint64", "name": "_deadline", "type": "uint64"},
        ],
        "name": "addLiquidity",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
AGNI_MINT_CALLBACK_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint256", "name": "_amount0Owed", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount1Owed", "type": "uint256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "name": "agniMintCallback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
AGNI_SWAP_CALLBACK_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int256", "name": "_amount0Delta", "type": "int256"},
            {"internalType": "int256", "name": "_amount1Delta", "type": "int256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "name": "agniSwapCallback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
ALL_POSITION_INFO_FUNCTION = Function(
    {
        "inputs": [],
        "name": "allPositionInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"internalType": "uint256", "name": "fee0", "type": "uint256"},
            {"internalType": "uint256", "name": "fee1", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
ALLOWANCE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
APPROVE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
ASSET_TOKEN0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "assetToken0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
ASSET_TOKEN1_FUNCTION = Function(
    {
        "inputs": [],
        "name": "assetToken1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
ASSIGN_MANAGER_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "_manager", "type": "address"}],
        "name": "assignManager",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
ASSIGN_ROUTER1_INCH_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "_router1Inch", "type": "address"}],
        "name": "assignRouter1Inch",
        "outputs": [],
        "stateMutability": "nonpayable",
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
CLIPPER_SWAP_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "clipperExchange", "type": "address"},
            {"internalType": "address", "name": "srcToken", "type": "address"},
            {"internalType": "address", "name": "dstToken", "type": "address"},
            {"internalType": "uint256", "name": "inputAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "outputAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "goodUntil", "type": "uint256"},
            {"internalType": "bytes32", "name": "r", "type": "bytes32"},
            {"internalType": "bytes32", "name": "vs", "type": "bytes32"},
        ],
        "name": "clipperSwap",
        "outputs": [{"internalType": "uint256", "name": "returnAmount", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
COLLECT_ALL_SWAP_FEE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "collectAllSwapFee",
        "outputs": [
            {"internalType": "uint128", "name": "amount0", "type": "uint128"},
            {"internalType": "uint128", "name": "amount1", "type": "uint128"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
COLLECT_MANAGEMENT_FEE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "collectManagementFee",
        "outputs": [{"internalType": "uint256", "name": "collectedShares", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
COLLECT_POSITION_SWAP_FEE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "_tickLower", "type": "int24"},
            {"internalType": "int24", "name": "_tickUpper", "type": "int24"},
        ],
        "name": "collectPositionSwapFee",
        "outputs": [
            {"internalType": "uint128", "name": "amount0", "type": "uint128"},
            {"internalType": "uint128", "name": "amount1", "type": "uint128"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
DECIMALS_FUNCTION = Function(
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    }
)
DECREASE_ALLOWANCE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "subtractedValue", "type": "uint256"},
        ],
        "name": "decreaseAllowance",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
DEPOSIT_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint256", "name": "_shares", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount0Max", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount1Max", "type": "uint256"},
        ],
        "name": "deposit",
        "outputs": [
            {"internalType": "uint256", "name": "depositedAmount0", "type": "uint256"},
            {"internalType": "uint256", "name": "depositedAmount1", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
ESTIMATED_VALUE_IN_TOKEN0_FUNCTION = Function(
    {
        "inputs": [],
        "name": "estimatedValueInToken0",
        "outputs": [{"internalType": "uint256", "name": "value0", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
ESTIMATED_VALUE_IN_TOKEN1_FUNCTION = Function(
    {
        "inputs": [],
        "name": "estimatedValueInToken1",
        "outputs": [{"internalType": "uint256", "name": "value1", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
FEE_CONFIG_FUNCTION = Function(
    {
        "inputs": [],
        "name": "feeConfig",
        "outputs": [
            {"internalType": "address", "name": "vault", "type": "address"},
            {"internalType": "uint24", "name": "entryFee", "type": "uint24"},
            {"internalType": "uint24", "name": "exitFee", "type": "uint24"},
            {"internalType": "uint24", "name": "performanceFee", "type": "uint24"},
            {"internalType": "uint24", "name": "managementFee", "type": "uint24"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_ALL_POSITIONS_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getAllPositions",
        "outputs": [
            {
                "components": [
                    {"internalType": "int24", "name": "tickLower", "type": "int24"},
                    {"internalType": "int24", "name": "tickUpper", "type": "int24"},
                    {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
                ],
                "internalType": "struct ITeaVaultV3Pair.Position[]",
                "name": "results",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_AMOUNTS_FOR_LIQUIDITY_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
        ],
        "name": "getAmountsForLiquidity",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_LIQUIDITY_FOR_AMOUNTS_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "name": "getLiquidityForAmounts",
        "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_POOL_INFO_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getPoolInfo",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint8", "name": "", "type": "uint8"},
            {"internalType": "uint8", "name": "", "type": "uint8"},
            {"internalType": "uint24", "name": "", "type": "uint24"},
            {"internalType": "uint160", "name": "", "type": "uint160"},
            {"internalType": "int24", "name": "", "type": "int24"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_TOKEN0_BALANCE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getToken0Balance",
        "outputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
GET_TOKEN1_BALANCE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "getToken1Balance",
        "outputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
INCREASE_ALLOWANCE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "addedValue", "type": "uint256"},
        ],
        "name": "increaseAllowance",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
INITIALIZE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "string", "name": "_name", "type": "string"},
            {"internalType": "string", "name": "_symbol", "type": "string"},
            {"internalType": "address", "name": "_factory", "type": "address"},
            {"internalType": "address", "name": "_token0", "type": "address"},
            {"internalType": "address", "name": "_token1", "type": "address"},
            {"internalType": "uint24", "name": "_feeTier", "type": "uint24"},
            {"internalType": "uint8", "name": "_decimalOffset", "type": "uint8"},
            {"internalType": "uint24", "name": "_feeCap", "type": "uint24"},
            {
                "components": [
                    {"internalType": "address", "name": "vault", "type": "address"},
                    {"internalType": "uint24", "name": "entryFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "exitFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "performanceFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "managementFee", "type": "uint24"},
                ],
                "internalType": "struct ITeaVaultV3Pair.FeeConfig",
                "name": "_feeConfig",
                "type": "tuple",
            },
            {"internalType": "address", "name": "_owner", "type": "address"},
        ],
        "name": "initialize",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
LAST_COLLECT_MANAGEMENT_FEE_FUNCTION = Function(
    {
        "inputs": [],
        "name": "lastCollectManagementFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
MANAGER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "manager",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
MULTICALL_FUNCTION = Function(
    {
        "inputs": [{"internalType": "bytes[]", "name": "data", "type": "bytes[]"}],
        "name": "multicall",
        "outputs": [{"internalType": "bytes[]", "name": "results", "type": "bytes[]"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
NAME_FUNCTION = Function(
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    }
)
OWNER_FUNCTION = Function(
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
POOL_FUNCTION = Function(
    {
        "inputs": [],
        "name": "pool",
        "outputs": [{"internalType": "contract IUniswapV3Pool", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
POSITION_INFO_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "_index", "type": "uint256"}],
        "name": "positionInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"internalType": "uint256", "name": "fee0", "type": "uint256"},
            {"internalType": "uint256", "name": "fee1", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
POSITION_INFO_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "_tickLower", "type": "int24"},
            {"internalType": "int24", "name": "_tickUpper", "type": "int24"},
        ],
        "name": "positionInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
            {"internalType": "uint256", "name": "fee0", "type": "uint256"},
            {"internalType": "uint256", "name": "fee1", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
POSITIONS_FUNCTION = Function(
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
PROXIABLE_UUID_FUNCTION = Function(
    {
        "inputs": [],
        "name": "proxiableUUID",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    }
)
REMOVE_LIQUIDITY_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "int24", "name": "_tickLower", "type": "int24"},
            {"internalType": "int24", "name": "_tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "_liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "_amount0Min", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount1Min", "type": "uint256"},
            {"internalType": "uint64", "name": "_deadline", "type": "uint64"},
        ],
        "name": "removeLiquidity",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
RENOUNCE_OWNERSHIP_FUNCTION = Function(
    {"inputs": [], "name": "renounceOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
)
ROUTER1_INCH_FUNCTION = Function(
    {
        "inputs": [],
        "name": "router1Inch",
        "outputs": [{"internalType": "contract IGenericRouter1Inch", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
SET_FEE_CONFIG_FUNCTION = Function(
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "vault", "type": "address"},
                    {"internalType": "uint24", "name": "entryFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "exitFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "performanceFee", "type": "uint24"},
                    {"internalType": "uint24", "name": "managementFee", "type": "uint24"},
                ],
                "internalType": "struct ITeaVaultV3Pair.FeeConfig",
                "name": "_feeConfig",
                "type": "tuple",
            }
        ],
        "name": "setFeeConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
SIMULATE_SWAP_INPUT_SINGLE_INTERNAL_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "bool", "name": "_zeroForOne", "type": "bool"},
            {"internalType": "uint256", "name": "_amountIn", "type": "uint256"},
        ],
        "name": "simulateSwapInputSingleInternal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
SWAP_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "executor", "type": "address"},
            {
                "components": [
                    {"internalType": "address", "name": "srcToken", "type": "address"},
                    {"internalType": "address", "name": "dstToken", "type": "address"},
                    {"internalType": "address payable", "name": "srcReceiver", "type": "address"},
                    {"internalType": "address payable", "name": "dstReceiver", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "minReturnAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "flags", "type": "uint256"},
                ],
                "internalType": "struct IGenericRouter1Inch.SwapDescription",
                "name": "desc",
                "type": "tuple",
            },
            {"internalType": "bytes", "name": "permit", "type": "bytes"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "swap",
        "outputs": [
            {"internalType": "uint256", "name": "returnAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "spentAmount", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
SWAP_INPUT_SINGLE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "bool", "name": "_zeroForOne", "type": "bool"},
            {"internalType": "uint256", "name": "_amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "_amountOutMin", "type": "uint256"},
            {"internalType": "uint160", "name": "_minPriceInSqrtPriceX96", "type": "uint160"},
            {"internalType": "uint64", "name": "_deadline", "type": "uint64"},
        ],
        "name": "swapInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
SWAP_OUTPUT_SINGLE_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "bool", "name": "_zeroForOne", "type": "bool"},
            {"internalType": "uint256", "name": "_amountOut", "type": "uint256"},
            {"internalType": "uint256", "name": "_amountInMax", "type": "uint256"},
            {"internalType": "uint160", "name": "_maxPriceInSqrtPriceX96", "type": "uint160"},
            {"internalType": "uint64", "name": "_deadline", "type": "uint64"},
        ],
        "name": "swapOutputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
SYMBOL_FUNCTION = Function(
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
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
TRANSFER_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
TRANSFER_FROM_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "transferFrom",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
TRANSFER_OWNERSHIP_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
UNISWAP_V3_SWAP_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "minReturn", "type": "uint256"},
            {"internalType": "uint256[]", "name": "pools", "type": "uint256[]"},
        ],
        "name": "uniswapV3Swap",
        "outputs": [{"internalType": "uint256", "name": "returnAmount", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
UNOSWAP_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "srcToken", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "minReturn", "type": "uint256"},
            {"internalType": "uint256[]", "name": "pools", "type": "uint256[]"},
        ],
        "name": "unoswap",
        "outputs": [{"internalType": "uint256", "name": "returnAmount", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
UPGRADE_TO_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "newImplementation", "type": "address"}],
        "name": "upgradeTo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
)
UPGRADE_TO_AND_CALL_FUNCTION = Function(
    {
        "inputs": [
            {"internalType": "address", "name": "newImplementation", "type": "address"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "upgradeToAndCall",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
)
VAULT_ALL_UNDERLYING_ASSETS_FUNCTION = Function(
    {
        "inputs": [],
        "name": "vaultAllUnderlyingAssets",
        "outputs": [
            {"internalType": "uint256", "name": "amount0", "type": "uint256"},
            {"internalType": "uint256", "name": "amount1", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
