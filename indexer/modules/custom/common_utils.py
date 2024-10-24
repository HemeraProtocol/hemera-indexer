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


def simple_get_rpc_requests(
    web3, make_requests, requests, is_batch, abi_list, fn_name, contract_address_key, batch_size, max_worker
):
    if len(requests) == 0:
        return []

    function_abi = next((abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"), None)
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    def process_batch(batch):
        parameters = build_no_input_method_data(web3, batch, fn_name, abi_list, contract_address_key)
        token_name_rpc = list(generate_eth_call_json_rpc(parameters))

        if is_batch:
            response = make_requests(params=json.dumps(token_name_rpc))
        else:
            response = [make_requests(params=json.dumps(token_name_rpc[0]))]

        token_infos = []
        for data in list(zip_rpc_response(parameters, response)):
            result = rpc_response_to_result(data[1])
            token = data[0]
            value = result[2:] if result is not None else None
            try:
                decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
                token[fn_name] = decoded_data[0]
            except Exception as e:
                logger.error(
                    f"Decoding {fn_name} failed. "
                    f"token: {token}. "
                    f"fn: {fn_name}. "
                    f"rpc response: {result}. "
                    f"exception: {e}"
                )
            token_infos.append(token)
        return token_infos

    executor = BatchWorkExecutor(
        starting_batch_size=batch_size,
        max_workers=max_worker,
        job_name=f"simple_get_rpc_requests_{fn_name}",
    )

    all_token_infos = []

    def work_handler(batch):
        nonlocal all_token_infos
        batch_results = process_batch(batch)
        all_token_infos.extend(batch_results)

    executor.execute(requests, work_handler, total_items=len(requests))
    executor.wait()

    return all_token_infos


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
