import flask
from flask_restx import Resource

from hemera.api.app.cache import cache
from hemera.api.app.contract import contract_namespace
from hemera.api.app.contract.contract_verify import (
    check_contract_verification_status,
    command_normal_contract_data,
    get_abi_by_chain_id_address,
    get_contract_by_address,
    get_contract_code_by_address,
    get_creation_or_deployed_code,
    get_evm_versions,
    get_explorer_license_type,
    get_implementation_contract,
    get_solidity_version,
    get_vyper_version,
    send_async_verification_request,
    send_sync_verification_request,
    validate_input,
)
from hemera.api.app.limiter import limiter
from hemera.common.models import db as postgres_db
from hemera.common.models.contracts import Contracts
from hemera.common.utils.exception_control import APIError
from hemera.common.utils.format_utils import as_dict, hex_str_to_bytes
from hemera.common.utils.web3_utils import ZERO_ADDRESS


@contract_namespace.route("/v1/explorer/verify_contract/verify")
@contract_namespace.route("/v2/explorer/verify_contract/verify")
class ExplorerVerifyContract(Resource):
    def post(_):
        request_form = flask.request.form
        address = request_form.get("address", "").lower()
        compiler_type = request_form.get("compiler_type")
        compiler_version = request_form.get("compiler_version")
        evm_version = request_form.get("evm_version")
        proxy = request_form.get("proxy")
        implementation = request_form.get("implementation")
        license_type = request_form.get("license_type", "None")
        optimization = request_form.get("optimization")
        optimization_runs = request_form.get("optimization_runs")
        constructor_arguments = request_form.get("constructor_arguments")
        file_list = flask.request.files.getlist("files")
        input_str = request_form.get("input_str")

        validate_input(address, compiler_type, compiler_version)

        contracts = get_contract_by_address(address)
        check_contract_verification_status(contracts)

        creation_code, deployed_code = get_creation_or_deployed_code(contracts)

        payload = {
            "address": address,
            "wallet_address": ZERO_ADDRESS,
            "compiler_type": compiler_type,
            "compiler_version": compiler_version,
            "evm_version": evm_version,
            "license_type": license_type,
            "optimization": optimization,
            "optimization_runs": optimization_runs,
            "input_str": input_str,
            "constructor_arguments": constructor_arguments,
            "proxy": proxy,
            "implementation": implementation,
            "creation_code": creation_code,
            "deployed_code": deployed_code,
        }

        if compiler_type != "Solidity (Standard-Json-Input)":
            libraries = request_form.get("libraries")
            payload["libraries_data"] = libraries

        response = send_sync_verification_request(payload, file_list)

        if response.status_code == 200:
            contracts.is_verified = True
            postgres_db.session.commit()
            return {"message": "Contract verified successfully"}, 200
        else:
            return {"message": f"Verified contract failed: {response.text}"}, 400


@contract_namespace.route("/v1/explorer/verify_contract/solidity_versions")
class ExplorerSolidityCompilerVersion(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self):
        response = get_solidity_version()
        if response:
            compiler_versions = response.get("compiler_versions")
            return {"compiler_versions": compiler_versions}, 200
        else:
            raise APIError("Failed to retrieve compiler versions", code=400)


@contract_namespace.route("/v1/explorer/verify_contract/compiler_types")
class ExplorerCompilerType(Resource):
    def get(self):
        compiler_types = [
            "Solidity (Single file)",
            "Solidity (Multi-Part files)",
            "Solidity (Standard-Json-Input)",
            "Vyper (Experimental)",
        ]
        return {"compiler_types": compiler_types}, 200


@contract_namespace.route("/v1/explorer/verify_contract/evm_versions")
class ExplorerEvmVersions(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self):
        evm_versions = get_evm_versions()
        if evm_versions:
            return evm_versions, 200
        raise APIError("Failed to retrieve evm versions", code=400)


@contract_namespace.route("/v1/explorer/verify_contract/license_types")
class ExplorerLicenseType(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self):
        license_type = get_explorer_license_type()
        if license_type:
            return license_type, 200
        raise APIError("Failed to retrieve license types", code=400)


@contract_namespace.route("/v1/explorer/verify_contract/vyper_versions")
class ExplorerVyperCompilerVersion(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self):
        response = get_vyper_version()
        if response:
            compiler_versions = response.get("compiler_versions")
            return {"compiler_versions": compiler_versions}, 200
        else:
            raise APIError("Failed to retrieve compiler versions", code=400)


@contract_namespace.route("/v1/explorer/verify_contract/check")
class ExplorerVerifyContractBeforeCheck(Resource):
    def post(self):
        request_body = flask.request.json
        address = request_body.get("address")

        if not address:
            raise APIError("Missing required data", code=400)
        address = address.lower()
        # Check if address exists in ContractsInfo
        contracts = postgres_db.session.query(Contracts).filter_by(address=hex_str_to_bytes(address)).first()

        if not contracts or not contracts.transaction_hash:
            raise APIError("The address is not a contract", code=400)

        if contracts.is_verified:
            return {
                "message": "This contract already verified",
                "already_verified": True,
            }, 200

        return {
            "message": "This contract can be verified",
            "already_verified": False,
        }, 200


@contract_namespace.route("/v1/explorer/verify_contract/verify_proxy")
class ExplorerVerifyContract(Resource):
    def post(self):
        request_body = flask.request.json
        proxy_contract_address = request_body.get("proxy_contract_address")
        if not proxy_contract_address:
            raise APIError("Please sent correct proxy contract address")

        implementation_address = get_implementation_contract(proxy_contract_address)
        print(implementation_address)
        if not implementation_address:
            return {
                "implementation_address": None,
                "message": "This contract does not look like it contains any delegatecall opcode sequence.",
            }
        exists = get_abi_by_chain_id_address(address=implementation_address)

        if not exists:
            return {
                "implementation_contract_address": implementation_address,
                "message": f"The implementation contract at {implementation_address} does not seem to be verified.",
                "is_verified": False,
            }

        return {
            "implementation_contract_address": implementation_address,
            "message": f"The proxy's implementation contract is found at: {implementation_address}.",
            "is_verified": True,
        }


@contract_namespace.route("/v1/explorer/verify_contract/save_proxy")
class ExplorerVerifyContract(Resource):
    def post(self):
        request_body = flask.request.json
        proxy_contract_address = request_body.get("proxy_contract_address")
        implementation_contract_address = request_body.get("implementation_contract_address")

        if not proxy_contract_address or not implementation_contract_address:
            raise APIError("Not such proxy contract address", code=400)

        contract = Contracts.query.filter(Contracts.address == proxy_contract_address.lower()).first()
        contract.verified_implementation_contract = implementation_contract_address.lower()

        postgres_db.session.add(contract)
        postgres_db.session.commit()
        return as_dict(contract)


@contract_namespace.route("/v1/explorer/command_api/contract")
class ExplorerContractCommandApi(Resource):
    def get(self):
        module = flask.request.args.get("module")
        action = flask.request.args.get("action")
        guid = flask.request.args.get("guid")
        address = flask.request.args.get("address")
        return command_normal_contract_data(module, action, address, guid)

    @limiter.limit("10 per minute")
    def post(self):
        request_form = flask.request.form
        action = request_form.get("action")
        module = request_form.get("module")
        if module != "contract":
            return {"message": "The module is error", "status": "0"}, 200

        if action != "verifysourcecode":
            guid = request_form.get("guid")
            address = request_form.get("address")
            return command_normal_contract_data(module, action, address, guid)

        address = request_form.get("contractaddress")
        address = address.lower()
        compiler_type = request_form.get("codeformat")
        compiler_version = request_form.get("compilerversion")
        optimization_used = request_form.get("optimizationUsed")
        if optimization_used == "1":
            optimization = True
        else:
            optimization = False
        optimization_runs = request_form.get("runs")
        if not optimization_runs:
            optimization_runs = 0
        input_str = request_form.get("sourceCode")
        constructor_arguments = request_form.get("constructorArguments")
        license_type = "None"
        evm_version = "default"

        contracts = get_contract_by_address(address)
        if contracts.is_verified:
            return {"message": "This contract is verified", "status": "0"}, 200

        creation_code, deployed_code = get_creation_or_deployed_code(contracts)
        payload = {
            "address": address,
            "compiler_type": compiler_type,
            "compiler_version": compiler_version,
            "evm_version": evm_version,
            "license_type": license_type,
            "optimization": optimization,
            "optimization_runs": optimization_runs,
            "input_str": input_str,
            "constructor_arguments": constructor_arguments,
            "creation_code": creation_code,
            "deployed_code": deployed_code,
        }

        response = send_async_verification_request(payload)

        if response.status_code == 202:
            # todo: use async way
            contracts.is_verified = True
            postgres_db.session.commit()
            return {
                "message": "Contract successfully verified",
                # "message": "Contract is being verified",
                "result": response.json()["guid"],
                "status": "1",
            }, 200
        else:
            return {
                "message": response.text,
                "status": "0",
            }, 200


@contract_namespace.route("/v1/explorer/contract/<contract_address>/code")
class ExplorerContractCode(Resource):
    def get(self, contract_address):
        contract_address = contract_address.lower()

        contract = Contracts.query.get(hex_str_to_bytes(contract_address))
        if not contract or contract.is_verified == False:
            raise APIError("Contract not exist or contract is not verified.", code=400)

        contracts_verification = get_contract_code_by_address(address=contract_address)
        if not contracts_verification:
            raise APIError("Contract code not found!", code=400)

        # need front to change
        files = []
        if "folder_path" in contracts_verification:
            for file in contracts_verification["folder_path"]:
                files.append(
                    {
                        "name": file.split("/")[-1],
                        "path": "https://contract-verify-files.s3.amazonaws.com/" + file,
                    }
                )
        contracts_verification["files"] = files
        return contracts_verification, 200
