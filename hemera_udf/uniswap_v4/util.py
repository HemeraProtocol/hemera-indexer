import logging

import hemera_udf.uniswap_v4.abi.uniswapv4_abi as uniswapv4_abi

logger = logging.getLogger(__name__)


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
            factory_address = job.get("factory_address").lower()
            position_token_address = job.get("position_token_address").lower()
            state_view_address = job.get("state_view_address", "").lower() if job.get("state_view_address") else None

            if factory_address not in self.factory_address_list:
                self.factory_address_list.append(factory_address)

            if position_token_address not in self.position_token_address_list:
                self.position_token_address_list.append(position_token_address)

            abi_module = self._get_abi_module(type_str)
            if abi_module not in self.abi_modules_list:
                self.abi_modules_list.append(abi_module)

            if not factory_address or not position_token_address or not abi_module:
                raise ValueError("Factory address, position token address, and ABI module are required")

            entry = {
                "position_token_address": position_token_address,
                "factory_address": factory_address,
                "type": type_str,
                "abi_module": abi_module,
                "state_view_address": state_view_address,
            }

            self.factory_to_position[factory_address] = entry
            self.position_to_factory[position_token_address] = entry

    def _get_abi_module(self, type_str):
        return {"uniswapv4": uniswapv4_abi}.get(type_str)

    def get_position_by_factory(self, factory_address):
        entry = self.factory_to_position.get(factory_address)
        return entry.get("position_token_address") if entry else None

    def get_factory_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry.get("factory_address") if entry else None

    def get_abi_by_factory(self, factory_address):
        entry = self.factory_to_position.get(factory_address)
        return entry.get("abi_module") if entry else None

    def get_abi_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry.get("abi_module") if entry else None

    def get_type_str_by_position(self, position_token_address):
        entry = self.position_to_factory.get(position_token_address)
        return entry.get("type") if entry else None

    def get_state_view_address(self, factory_address):
        """
        Get the StateView contract address for a factory.
        The StateView contract provides utility functions to query pool state.
        """
        entry = self.factory_to_position.get(factory_address)
        return entry.get("state_view_address") if entry else None
