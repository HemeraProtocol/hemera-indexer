from common.utils.abi_code_utils import Event, Function

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
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": true, "internalType": "uint16", "name": "_referral", "type": "uint16"},
            {"indexed": false, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
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
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_borrowRateMode", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_borrowRate", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_originationFee", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_borrowBalanceIncrease", "type": "uint256"},
            {"indexed": true, "internalType": "uint16", "name": "_referral", "type": "uint16"},
            {"indexed": false, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "Borrow",
        "type": "event",
    }
)

REPAY_EVENT = Event(
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_repayer", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "_amountMinusFees", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_fees", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_borrowBalanceIncrease", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "Repay",
        "type": "event",
    }
)

FLUSH_LOAN_EVENT = Event(
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "_target", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_totalFee", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_protocolFee", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "FlashLoan",
        "type": "event",
    }
)

LIQUIDATION_CALL_EVENT = Event(
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "_collateral", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_reserve", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "_user", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "_purchaseAmount", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_liquidatedCollateralAmount", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "_accruedBorrowInterest", "type": "uint256"},
            {"indexed": false, "internalType": "address", "name": "_liquidator", "type": "address"},
            {"indexed": false, "internalType": "bool", "name": "_receiveAToken", "type": "bool"},
            {"indexed": false, "internalType": "uint256", "name": "_timestamp", "type": "uint256"},
        ],
        "name": "LiquidationCall",
        "type": "event",
    }
)
