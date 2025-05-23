from hemera.common.utils.abi_code_utils import Event, Function

SCALED_BALANCE_OF_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "scaledBalanceOf",
        "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)
PRINCIPAL_BALANCE_OF_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "principalBalanceOf",
        "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

DECIMALS_FUNCTIOIN = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "decimals", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

SYMBOL_FUNCTIOIN = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "symbol", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

RESERVE_INITIALIZED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "asset", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "aToken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "stableDebtToken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "variableDebtToken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "interestRateStrategyAddress", "type": "address"},
        ],
        "name": "ReserveInitialized",
        "type": "event",
    }
)

DEPOSIT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "reserve", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "onBehalfOf", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": True, "internalType": "uint16", "name": "referral", "type": "uint16"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

WITHDRAW_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "Withdraw",
        "type": "event",
    }
)

BORROW_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "puinternalType": "address", "name": "reserve", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "onBehalfOf", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "borrowRateMode", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "borrowRate", "type": "uint256"},
            {"indexed": True, "internalType": "uint16", "name": "referral", "type": "uint16"},
        ],
        "name": "Borrow",
        "type": "event",
    }
)

REPAY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "repayer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "Repay",
        "type": "event",
    }
)

FLUSH_LOAN_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "initiator", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "asset", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "premium", "type": "uint256"},
            {"indexed": False, "internalType": "uint16", "name": "referralCode", "type": "uint16"},
        ],
        "name": "FlashLoan",
        "type": "event",
    }
)

LIQUIDATION_CALL_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "collateralAsset", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "debtAsset", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "debtToCover", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "liquidatedCollateralAmount", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
            {"indexed": False, "internalType": "bool", "name": "receiveAToken", "type": "bool"},
        ],
        "name": "LiquidationCall",
        "type": "event",
    }
)

RESERVE_DATA_UPDATED_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "reserve", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
        ],
        "name": "ReserveDataUpdated",
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
