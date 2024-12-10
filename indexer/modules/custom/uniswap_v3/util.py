import logging

from web3 import Web3

import indexer.modules.custom.uniswap_v3.agni_abi as agni_abi
import indexer.modules.custom.uniswap_v3.swapsicle_abi as swapsicle_abi
import indexer.modules.custom.uniswap_v3.uniswapv3_abi as uniswapv3_abi

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


class AddressManager:
    def __init__(self, jobs):
        # for filter topics
        self.abi_modules_list = []
        self.factory_address_list = []
        self.position_token_address_list = []

        self.factory_to_position = {}
        self.position_to_factory = {}

        self._build_mappings(jobs)

    def _build_mappings(self, jobs):
        for job in jobs:
            type_str = job.get("type")
            factory_address = job.get("factory address")
            position_token_address = job.get("position_token_address")

            if factory_address not in self.factory_address_list:
                self.factory_address_list.append(factory_address)

            if position_token_address not in self.position_token_address_list:
                self.position_token_address_list.append(position_token_address)

            abi_module = self._get_abi_module(type_str)
            if abi_module not in self.abi_modules_list:
                self.abi_modules_list.append(abi_module)

            if not factory_address or not position_token_address or not abi_module:
                raise ValueError("Factory address, position token address, and ABI module are required")

            self.factory_to_position[factory_address] = {
                "position_token_address": position_token_address,
                "type": type_str,
                "abi_module": abi_module,
            }
            self.position_to_factory[position_token_address] = {
                "factory_address": factory_address,
                "type": type_str,
                "abi_module": abi_module,
            }

    def _get_abi_module(self, type_str):
        abi_mapping = {
            "uniswapv3": uniswapv3_abi,
            "swapsicle": swapsicle_abi,
            "agni": agni_abi,
        }
        return abi_mapping.get(type_str)

    def get_position_by_factory(self, factory_address):
        entry = self.factory_to_position.get(factory_address)
        return entry.get("position_token_address") if entry else None

    def get_factory_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry.get("factory_address") if entry else None

    def get_abi_by_factory(self, factory_address):
        entry = self.factory_to_position.get(factory_address)
        return entry["abi_module"] if entry else None

    def get_abi_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry["abi_module"] if entry else None

    def get_type_str_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry["type"] if entry else None


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
