from common.utils.abi_code_utils import Event, Function

USER_BORROW_BALANCE_FUNCTION = Function(
    {
        "constant": True,
        "inputs": [
            {"internalType": "address", "name": "_reserve", "type": "address"},
            {"internalType": "address", "name": "_user", "type": "address"},
        ],
        "name": "getUserBorrowBalances",
        "outputs": [
            {"internalType": "uint256", "name": "principal_balance", "type": "uint256"},
            {"internalType": "uint256", "name": "compounded_balance", "type": "uint256"},
            {"internalType": "uint256", "name": "increase_balance", "type": "uint256"},
        ],
        "payable": False,
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
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_mToken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "_interestRateStrategyAddress", "type": "address"},
        ],
        "name": "ReserveInitialized",
        "type": "event",
    }
)

DEPOSIT_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": True, "internalType": "uint16", "name": "_referral", "type": "uint16"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

REDEEM_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "RedeemUnderlying",
        "type": "event",
    }
)

BORROW_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_borrowRateMode", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_borrowRate", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_originationFee", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_borrowBalanceIncrease", "type": "uint256"},
            {"indexed": True, "internalType": "uint16", "name": "_referral", "type": "uint16"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "Borrow",
        "type": "event",
    }
)

REPAY_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_repayer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amountMinusFees", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_fees", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_borrowBalanceIncrease", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "Repay",
        "type": "event",
    }
)

FLUSH_LOAN_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_target", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_totalFee", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_protocolFee", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "FlashLoan",
        "type": "event",
    }
)

LIQUIDATION_CALL_EVENT = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "_collateral", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "_purchaseAmount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_liquidatedCollateralAmount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_accruedBorrowInterest", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "_liquidator", "type": "address"},
            {"indexed": False, "internalType": "bool", "name": "_receiveAToken", "type": "bool"},
            {"indexed": False, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "LiquidationCall",
        "type": "event",
    }
)

RESERVE_UPDATED_EVENT = Event(
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
        "name": "ReserveUpdated",
        "type": "event",
    }
)
