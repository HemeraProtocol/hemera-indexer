import logging

from web3 import Web3

logger = logging.getLogger(__name__)


class BiDirectionalDict:
    def __init__(self, initial_dict=None):
        self.forward = initial_dict or {}
        self.backward = {v: k for k, v in self.forward.items()}

    def add(self, key, value):
        self.forward[key] = value
        self.backward[value] = key

    def get_forward(self, key):
        return self.forward.get(key)

    def get_backward(self, value):
        return self.backward.get(value)


# todo: remove
def build_no_input_method_data(web3, requests, fn, abi_list, contract_address_key="pool_address"):
    parameters = []

    for idx, token in enumerate(requests):
        token["request_id"] = idx
        token_data = {
            "request_id": idx,
            "param_to": token[contract_address_key],
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)
        try:
            # Encode the ABI for the specific token_id
            token["param_data"] = web3.eth.contract(
                address=Web3.to_checksum_address(token[contract_address_key]), abi=abi_list
            ).encodeABI(fn_name=fn)
        except Exception as e:
            logger.error(
                f"Encoding for function {fn} failed. "
                f"Contract address: {token[contract_address_key]}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters
