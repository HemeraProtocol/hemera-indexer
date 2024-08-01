import hashlib
from typing import List, Tuple

import requests

from common.models import db
from common.models.contracts import Contracts
from common.utils.config import get_config
from common.utils.exception_control import APIError
from common.utils.web3_utils import get_code, get_storage_at

config = get_config()

VERIFY_HOST = config.contract_service or ""
VERIFY_SERVICE_VALIDATION = VERIFY_HOST is not None and VERIFY_HOST != ""

NORMAL_TIMEOUT = 0.5
VERIFY_TIMEOUT = 30

CONTRACT_VERIFY_URL = f"{VERIFY_HOST}/v1/contract_verify/sync_verify"
COMMON_CONTRACT_VERIFY_URL = f"{VERIFY_HOST}/v1/contract_verify/async_verify"
ABI_HOST = f"{VERIFY_HOST}/v1/contract_verify/method"


def initial_chain_id():
    try:
        CHAIN_ID = config.chain_id
    except AttributeError:
        from common.utils.web3_utils import w3

        CHAIN_ID = w3.eth.chain_id
    return CHAIN_ID


CHAIN_ID = initial_chain_id()


class MockResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code


def get_sha256_hash(input_string):
    sha256 = hashlib.sha256()
    sha256.update(input_string.encode("utf-8"))
    return sha256.hexdigest()


def get_json_response_from_contract_verify_service(endpoint):
    if not VERIFY_SERVICE_VALIDATION:
        return []

    request_url = f"{VERIFY_HOST}{endpoint}"
    try:
        response = requests.get(request_url, timeout=NORMAL_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []


# ==========================
# 1. verify function
# ==========================


def validate_input(address, compiler_type, compiler_version):
    if not address or not compiler_type or not compiler_version:
        raise APIError("Missing base required data", code=400)


def get_contract_by_address(address: str):
    contract = db.session().query(Contracts).filter_by(address=address).first()
    if not contract:
        raise APIError("The address is not a contract", code=400)
    return contract


def check_contract_verification_status(contract):
    if contract.is_verified:
        raise APIError("This contract is already verified", code=400)


def get_creation_or_deployed_code(contract: Contracts):
    creation_code = None
    deployed_code = None
    if contract.creation_code:
        creation_code = "0x" + contract.creation_code.hex()
    if contract.deployed_code:
        deployed_code = "0x" + contract.deployed_code.hex()

    if not creation_code:
        creation_code = contract.bytecode
    if not deployed_code:
        deployed_code = get_code(contract.address)
    return creation_code, deployed_code


def send_sync_verification_request(payload, file_list):
    if not VERIFY_SERVICE_VALIDATION:
        return MockResponse("No valid verify service is set", 400)

    payload["chain_id"] = CHAIN_ID
    files = [("files", (file.filename, file.read(), "application/octet-stream")) for file in file_list]
    try:
        return requests.post(CONTRACT_VERIFY_URL, data=payload, files=files, timeout=VERIFY_TIMEOUT)
    except Exception as e:
        return MockResponse(str(e), 400)


def send_async_verification_request(payload):
    if not VERIFY_SERVICE_VALIDATION:
        return MockResponse("No valid verify service is set", 400)

    payload["chain_id"] = CHAIN_ID
    compiler_type = payload["compiler_type"]
    files = []
    if compiler_type == "solidity-standard-json-input":
        payload["compiler_type"] = "Solidity (Standard-Json-Input)"
        files = [("files", (payload["address"] + ".json", payload["input_str"], "application/octet-stream"))]


def get_abis_for_method(address_signed_prefix_list: List[Tuple[str, str]]):
    enrich_address_signed_prefix_list = [(l[0], l[1], 0) for l in address_signed_prefix_list]
    return get_abis_by_address_signed_prefix(enrich_address_signed_prefix_list)


def command_normal_contract_data(module, action, address, guid):
    if not VERIFY_SERVICE_VALIDATION:
        return {"message": "No valid verify service is set", "status": "0"}, 200


def get_abis_by_address_signed_prefix(address_signed_prefix_list: List[Tuple[str, str, int]]):
    result_list = []
    for address, signed_prefix, indexed_true_count in address_signed_prefix_list:
        contract = db.session.query(Contracts).get(bytes(address, "utf-8"))
        signed_prefix = signed_prefix
        if not contract:
            continue
        deployed_code_hash = contract.deployed_code.decode("utf-8")
        if contract.is_proxy:
            if not contract.implementation_contract:
                implementation_contract_address = get_implementation_contract(address)
                contract.implementation_contract = bytes(implementation_contract_address, "utf-8")
                db.session.commit()
            else:
                implementation_contract_address = contract.implementation_contract
            implementation_contract = db.session.query(Contracts).get(implementation_contract_address)
            if implementation_contract:
                implementation_deployed_hash = implementation_contract.deployed_code.decode("utf-8")
                result_list.append(
                    (1, indexed_true_count, address, (deployed_code_hash, implementation_deployed_hash), signed_prefix)
                )
            else:
                result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))
        else:
            result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))

    request_json = {"request_type": 1, "request_list": result_list}

    response = requests.post(url=ABI_HOST, json=request_json)
    if response.status_code == 200:
        return {(address, topic0): result_map for address, topic0, result_map in response.json()}
    return {}


def get_json_response_from_contract_verify_service(endpoint):
    request_url = f"{VERIFY_HOST}{endpoint}"
    response = requests.get(request_url)
    if response.status_code == 200:
        return response.json()
    else:
        return []


def get_contract_code_by_address(address):
    endpoint = f"/v1/contract_verify/{CHAIN_ID}/{address}/code"
    return get_json_response_from_contract_verify_service(endpoint)


def get_similar_addresses(deployed_code_hash):
    endpoint = f"/v1/contract_verify/similar_address/{CHAIN_ID}/{deployed_code_hash}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_solidity_version():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/solidity_versions")


def get_vyper_version():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/vyper_versions")


def get_evm_versions():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/evm_versions")


def get_explorer_license_type():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/license_types")


def get_abi_by_chain_id_address(address):
    endpoint = f"/v1/contract_verify/contract_abi/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_contract_verification_abi_by_address(address):
    endpoint = f"/v1/contract_verify/contract_verification_abi/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_check_verified_status(guid):
    endpoint = f"/v1/contract_verify/get_verified_status/{CHAIN_ID}/{guid}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_contract_verification_history_by_address(address):
    endpoint = f"/v1/contract_verify/get_verification_history/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def command_normal_contract_data(module, action, address, guid):
    if module != "contract":
        return {"message": "The parameter is error", "status": "0"}, 200
    if action == "getabi":
        if not address:
            return {"message": "the address is must input", "status": "0"}, 200
        address = address.lower()
        contracts = get_contract_verification_abi_by_address(address)
        if not contracts:
            return {
                "message": "Contract source code not verified",
                "status": "0",
            }, 200
        else:
            return {
                "message": "OK",
                "status": "1",
                "result": contracts.get("abi"),
            }, 200
    elif action == "checkverifystatus":
        if not guid:
            return {"message": "the guid is must input", "status": "0"}, 200
        history = get_check_verified_status(guid)
        if not history:
            return {"message": "the guid is error", "status": "0"}, 200
        if history["status"] == "SUCCESS":
            return {
                "message": "OK",
                "result": "Pass - Verified",
                "status": "1",
            }, 200
        elif history["status"] == "FAILED":
            return {
                "message": "NOK",
                "result": "Fail - Unable to verify",
                "status": "0",
            }, 200
        else:
            return {
                "message": "NOK",
                "result": "Unknown UID",
                "status": "0",
            }, 200
    return {"message": "the action is error", "status": "0"}, 200


def get_solidity_version():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/solidity_versions")


def get_vyper_version():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/vyper_versions")


def get_evm_versions():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/evm_versions")


def get_explorer_license_type():
    return get_json_response_from_contract_verify_service("/v1/contract_verify/license_types")


# ==========================
# 2. get info from a contract
# ==========================


def get_contract_code_by_address(address):
    endpoint = f"/v1/contract_verify/{CHAIN_ID}/{address}/code"
    return get_json_response_from_contract_verify_service(endpoint)


def get_similar_addresses(deployed_code_hash):
    endpoint = f"/v1/contract_verify/similar_address/{CHAIN_ID}/{deployed_code_hash}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_abi_by_chain_id_address(address):
    endpoint = f"/v1/contract_verify/contract_abi/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_contract_verification_abi_by_address(address):
    endpoint = f"/v1/contract_verify/contract_verification_abi/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_check_verified_status(guid):
    endpoint = f"/v1/contract_verify/get_verified_status/{CHAIN_ID}/{guid}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_contract_verification_history_by_address(address):
    endpoint = f"/v1/contract_verify/get_verification_history/{CHAIN_ID}/{address}"
    return get_json_response_from_contract_verify_service(endpoint)


def get_implementation_contract(address):
    implementation_address = None
    for code in [
        "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
        "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",
        "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7",
        "0x5f3b5dfeb7b28cdbd7faba78963ee202a494e2a2cc8c9978d5e30d2aebb8c197",
        #     add 5st
    ]:
        contract_address = get_storage_at(address, code)
        if contract_address and contract_address != "0x0000000000000000000000000000000000000000":
            implementation_address = contract_address
    return implementation_address


# ==========================
# 3. get method/log/contract name for a contract
# ==========================
def get_contract_names(address_list: list[str]) -> dict[str:str]:
    if not VERIFY_SERVICE_VALIDATION:
        return []

    CONTRACT_NAME_URL = f"{VERIFY_HOST}/v1/contract_verify/get_contract_name"
    request_json = {
        "chain_id": CHAIN_ID,
        "address_list": address_list,
    }
    try:
        response = requests.post(CONTRACT_NAME_URL, json=request_json, timeout=NORMAL_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []


def get_names_from_method_or_topic_list(method_list):
    if not VERIFY_SERVICE_VALIDATION:
        return []

    request_json = {"request_type": 0, "method_list": method_list}
    try:
        response = requests.post(url=ABI_HOST, json=request_json, timeout=NORMAL_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def get_abis_for_method(address_signed_prefix_list: List[Tuple[str, str]]):
    if not VERIFY_SERVICE_VALIDATION:
        return {}
    enrich_address_signed_prefix_list = [(l[0], l[1], 0) for l in address_signed_prefix_list]
    return get_abis_by_address_signed_prefix(enrich_address_signed_prefix_list)


def get_abis_for_logs(address_signed_prefix_list: List[Tuple[str, str, int]]):
    if not VERIFY_SERVICE_VALIDATION:
        return {}
    return get_abis_by_address_signed_prefix(address_signed_prefix_list)


def get_abis_by_address_signed_prefix(address_signed_prefix_list: List[Tuple[str, str, int]]):
    result_list = []
    for address, signed_prefix, indexed_true_count in address_signed_prefix_list:
        contract = db.session.query(Contracts).get(address)
        if not contract:
            continue
        deployed_code_hash = contract.deployed_code_hash

        if contract.is_proxy:
            if not contract.implementation_contract:
                implementation_contract_address = get_implementation_contract(address)
                contract.implementation_contract = implementation_contract_address
                db.session.commit()
            else:
                implementation_contract_address = contract.implementation_contract
            implementation_contract = db.session.query(Contracts).get(implementation_contract_address)
            if implementation_contract:
                implementation_deployed_hash = implementation_contract.deployed_code_hash
                result_list.append(
                    (1, indexed_true_count, address, (deployed_code_hash, implementation_deployed_hash), signed_prefix)
                )
            else:
                result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))
        else:
            result_list.append((0, indexed_true_count, address, deployed_code_hash, signed_prefix))

    request_json = {"request_type": 1, "request_list": result_list}

    try:
        response = requests.post(url=ABI_HOST, json=request_json, timeout=NORMAL_TIMEOUT)
        if response.status_code == 200:
            return {(address, topic0): result_map for address, topic0, result_map in response.json()}
        return {}
    except Exception:
        return {}
