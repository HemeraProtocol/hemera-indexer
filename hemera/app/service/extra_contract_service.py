#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/25 14:39
# @Author  ideal93
# @File  extra_contract_service.py
# @Brief

from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select

from hemera.app.utils.web3_utils import get_code, get_storage_at, w3
from hemera.common.models.contracts import Contracts
from hemera.common.utils.exception_control import APIError
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


class ExtraContractService:
    """Service class for handling contract verification and related operations"""

    def __init__(self, contract_service):
        self.verify_host = contract_service or ""
        self.verify_service_validation = bool(self.verify_host and self.verify_host != "")

        # Constants
        self.NORMAL_TIMEOUT = 0.5
        self.VERIFY_TIMEOUT = 30
        self.chain_id = self._initial_chain_id()

        # URLs
        self._setup_urls()

    def _initial_chain_id(self) -> int:
        """Initialize chain ID from config or web3"""
        return w3.eth.chain_id

    def _setup_urls(self):
        """Setup service URLs"""
        self.contract_verify_url = f"{self.verify_host}/v1/contract_verify/sync_verify"
        self.common_contract_verify_url = f"{self.verify_host}/v1/contract_verify/async_verify"
        self.abi_host = f"{self.verify_host}/v1/contract_verify/method"

    def _get_json_response(self, endpoint: str) -> List[Any]:
        """Generic method to get JSON response from contract verify service"""
        if not self.verify_service_validation:
            return []

        request_url = f"{self.verify_host}{endpoint}"
        try:
            response = requests.get(request_url, timeout=self.NORMAL_TIMEOUT)
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    # Contract Verification Methods
    def validate_verify_input(self, address: str, compiler_type: str, compiler_version: str):
        """Validate contract verification input parameters"""
        if not address or not compiler_type or not compiler_version:
            raise APIError("Missing base required data", code=400)

    def get_contract(self, session: Session, address: str) -> Contracts:
        """Get contract by address"""
        if isinstance(address, str):
            address = hex_str_to_bytes(address)
        contract = session.exec(select(Contracts).where(Contracts.address == address)).first()
        if not contract:
            raise APIError("The address is not a contract", code=400)
        return contract

    def check_verification_status(self, contract: Contracts):
        """Check if contract is already verified"""
        if contract.is_verified:
            raise APIError("This contract is already verified", code=400)

    def get_contract_code(self, contract: Contracts) -> Tuple[Optional[str], Optional[str]]:
        """Get creation and deployed code for a contract"""
        creation_code = bytes_to_hex_str(contract.creation_code) if contract.creation_code else contract.bytecode
        deployed_code = (
            bytes_to_hex_str(contract.deployed_code) if contract.deployed_code else get_code(contract.address)
        )
        return creation_code, deployed_code

    def send_sync_verification(self, payload: Dict[str, Any], file_list: List[Any]) -> requests.Response:
        """Send synchronous verification request"""
        if not self.verify_service_validation:
            return self._mock_response("No valid verify service is set", 400)

        payload["chain_id"] = self.chain_id
        files = [("files", (file.filename, file.read(), "application/octet-stream")) for file in file_list]

        try:
            return requests.post(self.contract_verify_url, data=payload, files=files, timeout=self.VERIFY_TIMEOUT)
        except Exception as e:
            return self._mock_response(str(e), 400)

    def send_async_verification(self, payload: Dict[str, Any]) -> requests.Response:
        """Send asynchronous verification request"""
        if not self.verify_service_validation:
            return self._mock_response("No valid verify service is set", 400)

        payload["chain_id"] = self.chain_id
        compiler_type = payload["compiler_type"]
        files = []

        if compiler_type == "solidity-standard-json-input":
            payload["compiler_type"] = "Solidity (Standard-Json-Input)"
            files = [("files", (payload["address"] + ".json", payload["input_str"], "application/octet-stream"))]
        elif compiler_type == "solidity-single-file":
            payload["compiler_type"] = "Solidity (Single file)"

        try:
            return requests.post(
                self.common_contract_verify_url, data=payload, files=files, timeout=self.VERIFY_TIMEOUT
            )
        except Exception as e:
            return self._mock_response(str(e), 400)

    # Version and Configuration Methods
    def get_solidity_versions(self) -> List[str]:
        """Get available Solidity versions"""
        return self._get_json_response("/v1/contract_verify/solidity_versions")

    def get_vyper_versions(self) -> List[str]:
        """Get available Vyper versions"""
        return self._get_json_response("/v1/contract_verify/vyper_versions")

    def get_evm_versions(self) -> List[str]:
        """Get available EVM versions"""
        return self._get_json_response("/v1/contract_verify/evm_versions")

    def get_license_types(self) -> List[str]:
        """Get available license types"""
        return self._get_json_response("/v1/contract_verify/license_types")

    # Contract Information Methods
    def get_contract_code_by_address(self, address: str) -> List[Any]:
        """Get contract code by address"""
        return self._get_json_response(f"/v1/contract_verify/{self.chain_id}/{address}/code")

    def get_similar_addresses(self, deployed_code_hash: str) -> List[str]:
        """Get similar contract addresses"""
        return self._get_json_response(f"/v1/contract_verify/similar_address/{self.chain_id}/{deployed_code_hash}")

    def get_contract_names(self, address_list: List[str]) -> Dict[str, str]:
        """Get contract names for a list of addresses"""
        if not self.verify_service_validation:
            return {}

        request_json = {
            "chain_id": self.chain_id,
            "address_list": address_list,
        }

        try:
            response = requests.post(
                f"{self.verify_host}/v1/contract_verify/get_contract_name",
                json=request_json,
                timeout=self.NORMAL_TIMEOUT,
            )
            return response.json() if response.status_code == 200 else {}
        except Exception:
            return {}

    # ABI Related Methods
    def get_abi_by_address(self, address: str) -> List[Any]:
        """Get ABI by address"""
        return self._get_json_response(f"/v1/contract_verify/contract_abi/{self.chain_id}/{address}")

    def get_verification_abi(self, address: str) -> Dict[str, Any]:
        """Get verification ABI by address"""
        return self._get_json_response(f"/v1/contract_verify/contract_verification_abi/{self.chain_id}/{address}")

    def get_verification_status(self, guid: str) -> Dict[str, Any]:
        """Get verification status by GUID"""
        return self._get_json_response(f"/v1/contract_verify/get_verified_status/{self.chain_id}/{guid}")

    def get_verification_history(self, address: str) -> List[Any]:
        """Get verification history by address"""
        return self._get_json_response(f"/v1/contract_verify/get_verification_history/{self.chain_id}/{address}")

    def get_implementation_contract(self, address: str) -> Optional[str]:
        """Get implementation contract address for proxy contracts"""
        storage_slots = [
            "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
            "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",
            "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7",
            "0x5f3b5dfeb7b28cdbd7faba78963ee202a494e2a2cc8c9978d5e30d2aebb8c197",
        ]

        for slot in storage_slots:
            contract_address = get_storage_at(address, slot)
            if contract_address and contract_address != "0x0000000000000000000000000000000000000000":
                return contract_address
        return None

    def get_abis_for_method(self, session, address_signed_prefix_list: List[Tuple[str, str]]) -> Dict[Any, Any]:
        """Get ABIs for methods

        Args:
            session: SQLModel session
            address_signed_prefix_list: List of tuples containing (address, signed_prefix)

        Returns:
            Dictionary containing ABI information for the methods
        """
        if not self.verify_service_validation:
            return {}
        enriched_list = [(addr, prefix, 0) for addr, prefix in address_signed_prefix_list]
        return self._get_abis_by_address_signed_prefix(session, enriched_list)

    def get_abis_for_logs(self, session, address_signed_prefix_list: List[Tuple[str, str, int]]) -> Dict[Any, Any]:
        """Get ABIs for logs

        Args:
            session: SQLModel session
            address_signed_prefix_list: List of tuples containing (address, signed_prefix, indexed_true_count)

        Returns:
            Dictionary containing ABI information for the logs
        """
        if not self.verify_service_validation:
            return {}
        return self._get_abis_by_address_signed_prefix(session, address_signed_prefix_list)

    def _get_abis_by_address_signed_prefix(
        self, session, address_signed_prefix_list: List[Tuple[str, str, int]]
    ) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Internal method to get ABIs by address and signed prefix

        Args:
            session: SQLModel session
            address_signed_prefix_list: List of tuples containing (address, signed_prefix, indexed_true_count)
                address: Contract address (hex string)
                signed_prefix: Method/event signature prefix
                indexed_true_count: Number of indexed parameters

        Returns:
            Dictionary mapping (address, topic0) pairs to their ABI information
        """
        result_list = []

        for address, signed_prefix, indexed_true_count in address_signed_prefix_list:
            contract = session.get(Contracts, hex_str_to_bytes(address))
            if not contract:
                continue

            deployed_code_hash = contract.deployed_code_hash

            if contract.is_proxy:
                if not contract.implementation_contract:
                    implementation_address = self.get_implementation_contract(address)
                    contract.implementation_contract = implementation_address
                    session.commit()
                else:
                    implementation_address = contract.implementation_contract

                implementation_contract = session.query(Contracts).get(implementation_address)
                if implementation_contract:
                    implementation_hash = implementation_contract.deployed_code_hash
                    result_list.append(
                        (1, indexed_true_count, address, (deployed_code_hash, implementation_hash), signed_prefix)
                    )
                else:
                    result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))
            else:
                result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))

        request_json = {"request_type": 1, "request_list": result_list}

        try:
            response = requests.post(url=self.abi_host, json=request_json, timeout=self.NORMAL_TIMEOUT)
            if response.status_code == 200:
                return {(address, topic0): result_map for address, topic0, result_map in response.json()}
            return {}
        except Exception:
            return {}

    @staticmethod
    def _mock_response(text: str, status_code: int) -> Any:
        """Create mock response for error cases"""

        class MockResponse:
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code

        return MockResponse(text, status_code)
