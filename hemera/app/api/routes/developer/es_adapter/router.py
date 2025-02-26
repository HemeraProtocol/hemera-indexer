#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/5 01:07
# @Author  ideal93
# @File  route.py
# @Brief

from enum import Enum
from typing import Dict, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import conint, constr, model_validator, validator

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.developer.es_adapter.helper import *

router = APIRouter(tags=["DEVELOPER"])


def limit_address_validator(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if not isinstance(value, str):
        raise ValueError("Invalid contract address format, must be a string.")
    if len(value) != 42:
        raise ValueError("Invalid contract address format, must be 42 characters long.")
    if not value.startswith("0x"):
        raise ValueError("Invalid contract address format, must start with '0x'.")
    if not all(c in "0123456789abcdefABCDEF" for c in value[2:]):
        raise ValueError("Invalid contract address format, must contain only hexadecimal characters.")
    return value.lower()


def limit_hash_validator(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if not isinstance(value, str):
        raise ValueError("Invalid hash format, must be a string.")
    if len(value) != 66:
        raise ValueError("Invalid hash format, must be 66 characters long.")
    if not value.startswith("0x"):
        raise ValueError("Invalid hash format, must start with '0x'.")
    if not all(c in "0123456789abcdefABCDEF" for c in value[2:]):
        raise ValueError("Invalid hash format, must contain only hexadecimal characters.")
    return value.lower()


class ModuleEnum(str, Enum):
    account = "account"
    contract = "contract"
    transaction = "transaction"
    block = "block"
    token = "token"
    logs = "logs"
    stats = "stats"


ALLOWED_ACTIONS: Dict[ModuleEnum, Set[str]] = {
    ModuleEnum.account: {
        "balance",
        "balancemulti",
        "balancehistory",
        "txlist",
        "txlistinternal",
        "tokentx",
        "tokennfttx",
        "tokenbalance",
        "tokenbalancehistory",
        "addresstokenbalance",
        "addresstokennftbalance",
        "addresstoken1155balance",
        "addresstokennftinventory",
    },
    ModuleEnum.transaction: {"getstatus", "gettxreceiptstatus"},
    ModuleEnum.logs: {"getLogs"},
    ModuleEnum.stats: {
        "tokensupply",
        "tokennftsupply",
        "token1155supply",
        "dailyavgblocktime",
        "dailyblkcount",
        "dailytxnfee",
        "dailynewaddress",
        "dailynetutilization",
        "dailytx",
        "dailyavgblocksize",
    },
    ModuleEnum.token: {"tokenholderlist", "tokeninfo"},
    ModuleEnum.block: {"getblocknobytime"},
    ModuleEnum.contract: {"getabi", "getcontractcreation", "getsourcecode"},
}


class DeveloperAPIRequest(BaseModel):
    module: ModuleEnum = Field(None, description="Module to query", example=ModuleEnum.account)
    action: Optional[str] = None
    tag: Optional[str] = None
    startblock: int = 0
    endblock: int = 99999999
    fromBlock: int = 0
    toBlock: int = 99999999
    startdate: Optional[datetime] = None
    enddate: Optional[datetime] = None
    tokenid: int = -1
    blockno: int = 0
    timestamp: int = 0
    closest: constr(pattern=r"^(before|after)$") = "before"
    page: conint(ge=1, le=1000) = 1
    offset: conint(ge=1, le=100) = 5
    sort: constr(pattern=r"^(asc|desc)$") = "asc"
    address: Optional[str] = None
    contractaddress: Optional[str] = None
    contractaddresses: Optional[List[str]] = None
    txhash: Optional[str] = None
    topic0: Optional[str] = None
    topic1: Optional[str] = None
    topic2: Optional[str] = None
    topic3: Optional[str] = None
    topic0_1_opr: constr(pattern=r"^(and|or)$") = "and"
    topic1_2_opr: constr(pattern=r"^(and|or)$") = "and"
    topic2_3_opr: constr(pattern=r"^(and|or)$") = "and"
    topic0_2_opr: constr(pattern=r"^(and|or)$") = "and"
    topic1_3_opr: constr(pattern=r"^(and|or)$") = "and"
    topic0_3_opr: constr(pattern=r"^(and|or)$") = "and"
    token_type: Optional[TokenType] = Field(None, description="Token type", example=TokenType.ERC20)

    @validator("txhash", pre=True, always=True)
    def validate_txhash(cls, value):
        return limit_hash_validator(value)

    @validator("address", "contractaddress", pre=True, always=True)
    def validate_address(cls, value):
        return limit_address_validator(value)

    @validator("contractaddresses", pre=True)
    def split_and_validate_addresses(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            addresses = value.split(",")
        elif isinstance(value, list):
            addresses = value
        else:
            raise ValueError("contractaddresses must be a comma separated string or a list of addresses")
        return [limit_address_validator(addr.strip()) for addr in addresses]

    @model_validator(mode="after")
    def check_module_action(self) -> "DeveloperAPIRequest":
        # Here, self is the model instance after individual validations have passed.
        if self.module is None:
            raise ValueError("The 'module' field is required")
        if self.action is None:
            raise ValueError("The 'action' field is required")
        allowed = ALLOWED_ACTIONS.get(self.module)
        if allowed is None:
            raise ValueError(f"No action list defined for module '{self.module}'")
        if self.action not in allowed:
            raise ValueError(f"For module '{self.module}', the action must be one of {allowed}")
        return self


@router.get("/v1/developer/api")
async def developer_api(session: ReadSessionDep, request: DeveloperAPIRequest = Depends()):
    module = request.module
    action = request.action

    if module == ModuleEnum.account:
        if action == "balance":
            result = account_balance(session, address=request.address)
        elif action == "balancemulti":
            result = account_balancemulti(session, addresses=request.contractaddresses)
        elif action == "balancehistory":
            result = account_balancehistory(session, address=request.address, blockno=request.blockno)
        elif action == "txlist":
            result = account_txlist(
                session,
                txhash=request.txhash,
                address=request.address,
                start_block=request.startblock,
                end_block=request.endblock,
                page=request.page,
                offset=request.offset,
                sort_order=request.sort,
            )
        elif action == "txlistinternal":
            result = account_txlistinternal(
                session,
                txhash=request.txhash,
                address=request.address,
                start_block=request.startblock,
                end_block=request.endblock,
                page=request.page,
                offset=request.offset,
                sort_order=request.sort,
            )
        elif action == "tokentx":
            result = get_account_token_transfers(
                session,
                contract_address=request.contractaddress,
                address=request.address,
                page=request.page,
                offset=request.offset,
                sort_order=request.sort,
                start_block=request.startblock,
                end_block=request.endblock,
                token_type=request.token_type,
            )
        elif action == "tokenbalance":
            result = account_token_balance(
                session,
                contract_address=request.contractaddress,
                address=request.address,
                token_type=request.token_type,
                token_id=request.tokenid,
            )
        elif action == "addresstokenbalance":
            result = account_address_token_holding(
                session,
                address=request.address,
                page=request.page,
                offset=request.offset,
                token_type=request.token_type,
            )
        elif action == "addresstokennftinventory":
            result = account_address_nft_inventory(
                session,
                address=request.address,
                contract_address=request.contractaddress,
                page=request.page,
                offset=request.offset,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action in account module")

    elif module == ModuleEnum.transaction:
        if action == "getstatus":
            result = check_contract_execution_status(session, txn_hash=request.txhash)
        elif action == "gettxreceiptstatus":
            result = check_transaction_receipt_status(session, txn_hash=request.txhash)
        else:
            raise HTTPException(status_code=400, detail="Invalid action in transaction module")

    elif module == ModuleEnum.logs:
        if action == "getLogs":
            result = get_event_logs(
                session,
                topic0=request.topic0,
                topic1=request.topic1,
                topic2=request.topic2,
                topic3=request.topic3,
                topic0_1_opr=request.topic0_1_opr,
                topic1_2_opr=request.topic1_2_opr,
                topic2_3_opr=request.topic2_3_opr,
                topic0_2_opr=request.topic0_2_opr,
                topic1_3_opr=request.topic1_3_opr,
                topic0_3_opr=request.topic0_3_opr,
                address=request.address,
                from_block=request.fromBlock,
                to_block=request.toBlock,
                page=request.page,
                offset=request.offset,
                sort_order=request.sort,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action in logs module")

    elif module == ModuleEnum.stats:
        if action == "tokensupply":
            result = stats_token_supply(session, contract_address=request.contractaddress)
        elif action == "dailytxnfee":
            result = stats_daily_network_transaction_fee(
                session, start_date=request.startdate, end_date=request.enddate, sort_order=request.sort
            )
        elif action == "dailynewaddress":
            result = stats_daily_new_address_count(
                session, start_date=request.startdate, end_date=request.enddate, sort_order=request.sort
            )
        elif action == "dailytx":
            result = stats_daily_transaction_count(
                session, start_date=request.startdate, end_date=request.enddate, sort_order=request.sort
            )
        elif action == "dailynetutilization":
            result = stats_daily_network_utilization(
                session, start_date=request.startdate, end_date=request.enddate, sort_order=request.sort
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action in stats module")

    elif module == ModuleEnum.token:
        if action == "tokeninfo":
            result = token_info(session, contract_address=request.contractaddress)
        elif action == "tokenholderlist":
            result = token_holder_list(
                session,
                contract_address=request.contractaddress,
                page=request.page,
                offset=request.offset,
                sort_order=request.sort,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid action in token module")

    elif module == ModuleEnum.block:
        if action == "getblocknobytime":
            result = block_number_by_timestamp(session, timestamp=request.timestamp, closest=request.closest)
        else:
            raise HTTPException(status_code=400, detail="Invalid action in block module")

    elif module == ModuleEnum.contract:
        if action == "getcontractcreation":
            result = get_contract_creator_and_creation_tx_hash(session, contract_addresses=request.contractaddresses)
        # elif action == "getabi":
        #     result = get_contract_abi(session, contract_address=request.address)
        # elif action == "getsourcecode":
        #     result = get_contract_source_code(session, contract_address=request.address)
        else:
            raise HTTPException(status_code=400, detail="Invalid action in contract module")
    else:
        raise HTTPException(status_code=400, detail="Invalid module")

    if not result:
        return {"status": "0", "message": "No data found"}
    return {"status": "1", "message": "OK", "result": result}
