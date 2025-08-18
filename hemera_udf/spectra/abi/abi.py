from hemera.common.utils.abi_code_utils import Event, Function


GET_BALANCES_FUNCTION = Function(
    {
        "inputs": [],
        "name": "get_balances",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    }
)