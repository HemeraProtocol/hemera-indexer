from common.utils.abi_code_utils import Function

get_shares_func = Function(
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "shares",
        "outputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
)

total_shares_func = Function(
    {
        "inputs": [],
        "name": "totalShares",
        "outputs": [{"internalType": "uint256", "name": "totalShares", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
)

total_value_in_lp_func = Function(
    {
        "inputs": [],
        "name": "totalValueInLp",
        "outputs": [{"name": "totalValueInLp", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    }
)

total_value_out_lp_func = Function(
    {
        "inputs": [],
        "name": "totalValueOutOfLp",
        "outputs": [{"name": "totalValueOutOfLp", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    }
)
