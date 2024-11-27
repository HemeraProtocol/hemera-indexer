import json
import logging
import os

from web3 import Web3

logger = logging.getLogger(__name__)


def load_abi(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, filename)
    with open(full_path, "r") as file:
        data = json.load(file)
    return data


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


def parse_hex_to_address(hex_string):
    hex_string = hex_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()


def parse_hex_to_int256(hex_string):
    value = Web3.to_int(hexstr=hex_string)
    if value >= 2**255:
        value -= 2**256
    return value
