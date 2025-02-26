from enum import Enum
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, and_, select

from hemera.app.api.deps import ReadSessionDep
from hemera.common.models.contracts import Contracts
from hemera.common.utils.format_utils import as_dict, hex_str_to_bytes
from hemera.common.utils.web3_utils import ZERO_ADDRESS

router = APIRouter(tags=["contracts"])


# Models
class CompilerVersionResponse(BaseModel):
    compiler_versions: List[str]


class VerifyContractRequest(BaseModel):
    address: str
    compiler_type: str
    compiler_version: str
    evm_version: Optional[str] = "default"
    proxy: Optional[str] = None
    implementation: Optional[str] = None
    license_type: str = "None"
    optimization: Optional[bool] = None
    optimization_runs: Optional[int] = None
    constructor_arguments: Optional[str] = None
    input_str: Optional[str] = None


class VerifyResponse(BaseModel):
    message: str
    status: Optional[str] = None
    result: Optional[str] = None


class CheckVerificationResponse(BaseModel):
    message: str
    already_verified: bool


class ProxyVerificationResponse(BaseModel):
    implementation_contract_address: Optional[str] = None
    implementation_address: Optional[str] = None
    message: str
    is_verified: Optional[bool] = None


# Contract Verification Endpoints
@router.post("/v1/explorer/verify_contract/verify", response_model=VerifyResponse)
async def verify_contract(
    session: ReadSessionDep,
    files: List[UploadFile] = File(None),
    address: str = Form(...),
    compiler_type: str = Form(...),
    compiler_version: str = Form(...),
    evm_version: Optional[str] = Form("default"),
    proxy: Optional[str] = Form(None),
    implementation: Optional[str] = Form(None),
    license_type: str = Form("None"),
    optimization: Optional[bool] = Form(None),
    optimization_runs: Optional[int] = Form(None),
    constructor_arguments: Optional[str] = Form(None),
    input_str: Optional[str] = Form(None),
):
    """Verify a smart contract with provided source code and compiler settings."""
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
        libraries = Form(None)
        if libraries:
            payload["libraries_data"] = libraries

    response = await send_sync_verification_request(payload, files)
    if response.status_code == 200:
        contracts.is_verified = True
        session.commit()
        return VerifyResponse(message="Contract verified successfully")

    return VerifyResponse(message=f"Verified contract failed: {response.text}")


@router.get("/v1/explorer/verify_contract/solidity_versions", response_model=CompilerVersionResponse)
async def get_solidity_compiler_versions():
    """Get supported Solidity compiler versions."""
    response = await get_solidity_version()
    if not response:
        raise HTTPException(status_code=400, detail="Failed to retrieve compiler versions")
    return CompilerVersionResponse(compiler_versions=response.get("compiler_versions"))


@router.get("/v1/explorer/verify_contract/compiler_types")
async def get_compiler_types():
    """Get available compiler types for smart contract verification."""
    return {
        "compiler_types": [
            "Solidity (Single file)",
            "Solidity (Multi-Part files)",
            "Solidity (Standard-Json-Input)",
            "Vyper (Experimental)",
        ]
    }


@router.get("/v1/explorer/verify_contract/evm_versions")
async def get_evm_version_list():
    """Get supported EVM versions for contract compilation."""
    evm_versions = await get_evm_versions()
    if not evm_versions:
        raise HTTPException(status_code=400, detail="Failed to retrieve evm versions")
    return evm_versions


@router.get("/v1/explorer/verify_contract/license_types")
async def get_license_types():
    """Get available license types for smart contracts."""
    license_types = await get_explorer_license_type()
    if not license_types:
        raise HTTPException(status_code=400, detail="Failed to retrieve license types")
    return license_types


@router.get("/v1/explorer/verify_contract/vyper_versions", response_model=CompilerVersionResponse)
async def get_vyper_compiler_versions():
    """Get supported Vyper compiler versions."""
    response = await get_vyper_version()
    if not response:
        raise HTTPException(status_code=400, detail="Failed to retrieve compiler versions")
    return CompilerVersionResponse(compiler_versions=response.get("compiler_versions"))


@router.post("/v1/explorer/verify_contract/check", response_model=CheckVerificationResponse)
async def check_contract_verification(session: ReadSessionDep, address: str):
    """Check if a contract is eligible for verification."""
    if not address:
        raise HTTPException(status_code=400, detail="Missing required data")

    address = address.lower()
    contract = session.exec(select(Contracts).where(Contracts.address == hex_str_to_bytes(address))).first()

    if not contract or not contract.transaction_hash:
        raise HTTPException(status_code=400, detail="The address is not a contract")

    if contract.is_verified:
        return CheckVerificationResponse(message="This contract already verified", already_verified=True)

    return CheckVerificationResponse(message="This contract can be verified", already_verified=False)


@router.post("/v1/explorer/verify_contract/verify_proxy", response_model=ProxyVerificationResponse)
async def verify_proxy_contract(
    proxy_contract_address: str,
):
    """Verify a proxy contract and get its implementation details."""
    if not proxy_contract_address:
        raise HTTPException(status_code=400, detail="Please sent correct proxy contract address")

    implementation_address = await get_implementation_contract(proxy_contract_address)
    if not implementation_address:
        return ProxyVerificationResponse(
            implementation_address=None,
            message="This contract does not look like it contains any delegatecall opcode sequence.",
        )

    exists = await get_abi_by_chain_id_address(address=implementation_address)
    return ProxyVerificationResponse(
        implementation_contract_address=implementation_address,
        message=f"The {'proxy' if exists else ''} implementation contract at {implementation_address} "
        f"{'is' if exists else 'is not'} verified.",
        is_verified=exists,
    )


@router.post("/v1/explorer/verify_contract/save_proxy")
async def save_proxy_mapping(
    session: ReadSessionDep,
    proxy_contract_address: str,
    implementation_contract_address: str,
):
    """Save the mapping between proxy and implementation contracts."""
    if not proxy_contract_address or not implementation_contract_address:
        raise HTTPException(status_code=400, detail="Not such proxy contract address")

    contract = session.exec(
        select(Contracts).where(Contracts.address == hex_str_to_bytes(proxy_contract_address.lower()))
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract.verified_implementation_contract = implementation_contract_address.lower()
    session.add(contract)
    session.commit()

    return as_dict(contract)


@router.get("/v1/explorer/command_api/contract")
async def command_contract_api(
    session: ReadSessionDep, module: str, action: str, guid: Optional[str] = None, address: Optional[str] = None
):
    """Query contract command API status."""
    return await command_normal_contract_data(module, action, address, guid)


@router.post("/v1/explorer/command_api/contract")
async def command_contract_verify(
    session: ReadSessionDep,
    action: str = Form(...),
    module: str = Form(...),
    contractaddress: Optional[str] = Form(None),
    codeformat: Optional[str] = Form(None),
    compilerversion: Optional[str] = Form(None),
    optimizationUsed: Optional[str] = Form(None),
    runs: Optional[int] = Form(None),
    sourceCode: Optional[str] = Form(None),
    constructorArguments: Optional[str] = Form(None),
    guid: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
):
    """Handle contract verification through command API."""
    if module != "contract":
        return {"message": "The module is error", "status": "0"}

    if action != "verifysourcecode":
        return await command_normal_contract_data(module, action, address, guid)

    address = contractaddress.lower()
    contracts = get_contract_by_address(address)
    if contracts.is_verified:
        return {"message": "This contract is verified", "status": "0"}

    creation_code, deployed_code = get_creation_or_deployed_code(contracts)
    payload = {
        "address": address,
        "compiler_type": codeformat,
        "compiler_version": compilerversion,
        "evm_version": "default",
        "license_type": "None",
        "optimization": True if optimizationUsed == "1" else False,
        "optimization_runs": runs or 0,
        "input_str": sourceCode,
        "constructor_arguments": constructorArguments,
        "creation_code": creation_code,
        "deployed_code": deployed_code,
    }

    response = await send_async_verification_request(payload)
    if response.status_code == 202:
        contracts.is_verified = True
        session.commit()
        return {"message": "Contract successfully verified", "result": response.json()["guid"], "status": "1"}
    return {"message": response.text, "status": "0"}


@router.get("/v1/explorer/contract/{contract_address}/code")
async def get_contract_code(session: ReadSessionDep, contract_address: str):
    """Get verified contract source code and related files."""
    contract_address = contract_address.lower()
    contract = session.get(Contracts, hex_str_to_bytes(contract_address))

    if not contract or not contract.is_verified:
        raise HTTPException(status_code=400, detail="Contract not exist or contract is not verified.")

    contracts_verification = await get_contract_code_by_address(address=contract_address)
    if not contracts_verification:
        raise HTTPException(status_code=400, detail="Contract code not found!")

    # Format file paths
    files = []
    if "folder_path" in contracts_verification:
        files = [
            {"name": file.split("/")[-1], "path": f"https://contract-verify-files.s3.amazonaws.com/{file}"}
            for file in contracts_verification["folder_path"]
        ]
    contracts_verification["files"] = files

    return contracts_verification
