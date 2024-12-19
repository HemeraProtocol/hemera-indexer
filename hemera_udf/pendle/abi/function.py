from hemera.common.utils.abi_code_utils import Function

get_sy_by_pt = Function(
    {
        "inputs": [],
        "name": "SY",
        "outputs": [{"internalType": "address", "name": "sy", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
get_yt_by_pt = Function(
    {
        "inputs": [],
        "name": "YT",
        "outputs": [{"internalType": "address", "name": "yt", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)

market_active_balance = Function(
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "activeBalance",
        "outputs": [{"internalType": "uint256", "name": "active_balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

market_total_active_supply = Function(
    {
        "inputs": [],
        "name": "totalActiveSupply",
        "outputs": [{"internalType": "uint256", "name": "total", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

yield_token_function = Function(
    {
        "inputs": [],
        "name": "yieldToken",
        "outputs": [{"internalType": "address", "name": "yield_token", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
)
