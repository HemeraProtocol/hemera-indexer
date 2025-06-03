from hemera.common.utils.abi_code_utils import Event, Function

token_create_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "creator", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "requestId", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "totalSupply", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "launchTime", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "launchFee", "type": "uint256"},
        ],
        "name": "TokenCreate",
        "type": "event",
    }
)

token_purchase_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "cost", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "fee", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "offers", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "funds", "type": "uint256"},
        ],
        "name": "TokenPurchase",
        "type": "event",
    }
)

token_sale_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "cost", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "fee", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "offers", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "funds", "type": "uint256"},
        ],
        "name": "TokenSale",
        "type": "event",
    }
)


GET_TOKEN_INFO_FUNCTION = Function(
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "getTokenInfo",
        "outputs": [
            {"internalType": "uint256", "name": "version", "type": "uint256"},
            {"internalType": "address", "name": "tokenManager", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "lastPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "tradingFeeRate", "type": "uint256"},
            {"internalType": "uint256", "name": "minTradingFee", "type": "uint256"},
            {"internalType": "uint256", "name": "launchTime", "type": "uint256"},
            {"internalType": "uint256", "name": "offers", "type": "uint256"},
            {"internalType": "uint256", "name": "maxOffers", "type": "uint256"},
            {"internalType": "uint256", "name": "funds", "type": "uint256"},
            {"internalType": "uint256", "name": "maxFunds", "type": "uint256"},
            {"internalType": "bool", "name": "liquidityAdded", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
)
