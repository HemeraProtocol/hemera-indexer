from common.utils.abi_code_utils import Function

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
