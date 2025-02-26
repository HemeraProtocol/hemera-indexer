import logging
from typing import cast

from eth_typing import ABIFunction

from hemera.common.utils.abi_code_utils import encode_data
from hemera.indexer.utils.abi import function_abi_to_4byte_selector_str

logger = logging.getLogger(__name__)


def get_chain_id(web3):
    return web3.eth.chain_id


# todo: remove later
def build_no_input_method_data(web3, requests, fn, abi_list, contract_address_key="pool_address", arguments=None):
    arguments = arguments or []

    parameters = []
    function_abi = next((abi for abi in abi_list if abi["name"] == fn and abi["type"] == "function"), None)
    abi_function = cast(ABIFunction, function_abi)
    for idx, token in enumerate(requests):
        # token["request_id"] = idx
        token_data = {
            "request_id": idx,
            "param_to": token[contract_address_key],
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)
        try:
            # Encode the ABI for the specific token_id
            token["param_data"] = encode_data(
                abi_function,
                arguments,
                function_abi_to_4byte_selector_str(abi_function),
            )
        except Exception as e:
            logger.error(
                f"Encoding for function {fn} failed. "
                f"Contract address: {token[contract_address_key]}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters
