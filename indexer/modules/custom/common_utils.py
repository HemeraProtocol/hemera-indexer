import json
import logging
from typing import cast

import eth_abi
from web3 import Web3
from web3.types import ABIFunction

from common.utils.abi_code_utils import encode_data
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.utils.abi import function_abi_to_4byte_selector_str
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

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


def build_one_input_one_output_method_data(web3, need_call_list, contract_address, fn, abi_list, data_key="token_id"):
    parameters = []
    contract = web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi_list)

    for idx, token in enumerate(need_call_list):
        token_data = {
            "request_id": idx,
            "param_to": contract_address,
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)

        try:
            data = contract.encodeABI(fn_name=fn, args=[token[data_key]])
            token["param_data"] = data
        except Exception as e:
            logger.error(
                f"Encoding token id {token[data_key]} for function {fn} failed. "
                f"contract address: {contract_address}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters
