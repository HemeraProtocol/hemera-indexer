#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/25 15:41
# @Author  ideal93
# @File  developer.py.py
# @Brief

import csv
import io
from datetime import date, datetime, time
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlmodel import Session, and_, func, or_, select

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.parameters.validate_address import external_api_validate_address
from hemera.common.models.blocks import Blocks
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.token_transfers import ERC20TokenTransfers, ERC721TokenTransfers, ERC1155TokenTransfers
from hemera.common.models.tokens import Tokens
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


def response_csv(data: list[dict], filename: str, header: list[str]) -> Response:
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=header)

    if header:
        cw.writeheader()

    cw.writerows(data)
    csv_content = si.getvalue()

    response = Response(content=csv_content, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


router = APIRouter(tags=["EXPORT"])


def get_block_range(
    session: ReadSessionDep,
    filtertype: Optional[str] = Query(
        None,
        regex="^(date|block)$",
        description="Query type: 'date' to filter by date range, 'block' to filter by block numbers",
    ),
    startblock: int = Query(0, ge=0, description="Start block number (used when filtertype is 'block')"),
    endblock: int = Query(4999, ge=0, description="End block number (used when filtertype is 'block')"),
    startdate: Optional[date] = Query(
        None, description="Start date in YYYY-MM-DD format (used when filtertype is 'date')"
    ),
    enddate: Optional[date] = Query(None, description="End date in YYYY-MM-DD format (used when filtertype is 'date')"),
) -> Tuple[int, int]:
    """
    Determine the block range. If filtertype=="date", convert the provided startdate and enddate
    into a block range using the Blocks table; otherwise, use the provided startblock and endblock.
    """
    if filtertype == "date":
        if not startdate or not enddate:
            raise HTTPException(
                status_code=400, detail="Start date and end date must be provided when using date filter"
            )
        start_timestamp = datetime.combine(startdate, time.min)
        end_timestamp = datetime.combine(enddate, time.max)
        start_block_obj = session.exec(
            select(Blocks).where(Blocks.timestamp >= start_timestamp).order_by(Blocks.timestamp.asc()).limit(1)
        ).first()
        end_block_obj = session.exec(
            select(Blocks).where(Blocks.timestamp <= end_timestamp).order_by(Blocks.timestamp.desc()).limit(1)
        ).first()
        start_block_number = start_block_obj.number if start_block_obj else 0
        end_block_number = end_block_obj.number if end_block_obj else 0
        return start_block_number, end_block_number
    else:
        return startblock, endblock


@router.get("/v1/explorer/export/transactions/{address}")
async def export_transactions(
    session: ReadSessionDep,
    address: str = Depends(external_api_validate_address),
    block_range: Tuple[int, int] = Depends(get_block_range),
):
    start_block_number, end_block_number = block_range

    stmt = (
        select(Transactions)
        .where(
            and_(
                Transactions.block_number >= start_block_number,
                Transactions.block_number <= end_block_number,
                or_(
                    Transactions.from_address == hex_str_to_bytes(address),
                    Transactions.to_address == hex_str_to_bytes(address),
                ),
            )
        )
        .order_by(Transactions.block_number.asc(), Transactions.transaction_index.asc())
        .limit(5000)
    )
    transactions: List[Transactions] = session.exec(stmt).all()

    header = [
        "blockNumber",
        "timeStamp",
        "hash",
        "nonce",
        "blockHash",
        "transactionIndex",
        "from",
        "to",
        "value",
        "gas",
        "gasPrice",
        "isError",
        "receiptStatus",
        "contractAddress",
        "cumulativeGasUsed",
        "gasUsed",
        "methodId",
    ]
    result = [
        {
            "blockNumber": str(tx.block_number),
            "timeStamp": tx.block_timestamp.strftime("%s"),
            "hash": bytes_to_hex_str(tx.hash),
            "nonce": str(tx.nonce),
            "blockHash": bytes_to_hex_str(tx.block_hash),
            "transactionIndex": str(tx.transaction_index),
            "from": bytes_to_hex_str(tx.from_address),
            "to": bytes_to_hex_str(tx.to_address),
            "value": str(tx.value),
            "gas": str(tx.gas),
            "gasPrice": str(tx.gas_price),
            "isError": "0" if tx.receipt_status == 1 else "1",
            "receiptStatus": str(tx.receipt_status),
            "contractAddress": bytes_to_hex_str(tx.receipt_contract_address) if tx.receipt_contract_address else "",
            "cumulativeGasUsed": str(tx.receipt_cumulative_gas_used),
            "gasUsed": str(tx.receipt_gas_used),
            "methodId": "0x" + tx.method_id if tx.method_id else "",
        }
        for tx in transactions
    ]
    filename = f"transactions-{address}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/internal_transactions/{address}")
async def export_internal_transactions(
    session: ReadSessionDep,
    address: str = Depends(external_api_validate_address),
    block_range: Tuple[int, int] = Depends(get_block_range),
):
    if not address:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    start_block_number, end_block_number = block_range

    stmt = (
        select(ContractInternalTransactions)
        .where(
            and_(
                ContractInternalTransactions.block_number >= start_block_number,
                ContractInternalTransactions.block_number <= end_block_number,
                or_(
                    ContractInternalTransactions.from_address == hex_str_to_bytes(address),
                    ContractInternalTransactions.to_address == hex_str_to_bytes(address),
                ),
            )
        )
        .order_by(ContractInternalTransactions.block_number.asc(), ContractInternalTransactions.transaction_index.asc())
        .limit(5000)
    )
    internal_transactions: List[ContractInternalTransactions] = session.exec(stmt).all()

    header = [
        "blockNumber",
        "timeStamp",
        "hash",
        "from",
        "to",
        "value",
        "contractAddress",
        "type",
        "gas",
        "traceId",
        "isError",
        "errCode",
    ]
    result = [
        {
            "blockNumber": str(tx.block_number),
            "timeStamp": tx.block_timestamp.strftime("%s"),
            "hash": tx.transaction_hash,
            "from": tx.from_address,
            "to": tx.to_address,
            "value": str(tx.value),
            "contractAddress": tx.to_address if tx.trace_type in ["create", "create2"] else "",
            "type": tx.trace_type,
            "gas": str(tx.gas),
            "traceId": tx.trace_id,
            "isError": "1" if tx.error == 0 else "0",
            "errCode": str(tx.error),
        }
        for tx in internal_transactions
    ]
    filename = f"internal_transactions-{address}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


def token_transfers(
    session: Session,
    contract_address: Optional[str],
    address: Optional[str],
    start_block_number: int,
    end_block_number: int,
    token_type: str,
) -> List[dict]:
    TokenTable = Tokens
    TokenTransferTable = {
        "ERC20": ERC20TokenTransfers,
        "ERC721": ERC721TokenTransfers,
        "ERC1155": ERC1155TokenTransfers,
    }[token_type]

    # Build filtering condition.
    condition = True
    if contract_address:
        condition = and_(condition, TokenTransferTable.token_address == hex_str_to_bytes(contract_address))
    if address:
        condition = and_(
            condition,
            or_(
                TokenTransferTable.from_address == hex_str_to_bytes(address),
                TokenTransferTable.to_address == hex_str_to_bytes(address),
            ),
        )
    if not address and not contract_address:
        raise HTTPException(status_code=400, detail="Error address")

    stmt = (
        select(
            TokenTransferTable,
            Transactions.nonce,
            Transactions.gas,
            Transactions.gas_price,
            Transactions.receipt_gas_used,
            Transactions.receipt_cumulative_gas_used,
            Transactions.transaction_index,
            Transactions.input,
        )
        .join(Transactions, TokenTransferTable.transaction_hash == Transactions.hash)
        .where(
            and_(
                condition,
                TokenTransferTable.block_number >= start_block_number,
                TokenTransferTable.block_number <= end_block_number,
            )
        )
        .order_by(TokenTransferTable.block_number.asc())
        .limit(5000)
    )
    transfers = session.exec(stmt).all()

    # Get token details for each unique token address.
    token_addresses = {transfer.token_address for transfer, *_ in transfers}
    tokens = session.exec(select(TokenTable).where(TokenTable.address.in_(token_addresses))).all()
    token_dict = {token.address: token for token in tokens}

    result = []
    for row in transfers:
        (
            transfer,
            nonce,
            gas,
            gas_price,
            receipt_gas_used,
            receipt_cumulative_gas_used,
            transaction_index,
            input_val,
        ) = row
        token_info = token_dict.get(transfer.token_address)
        transfer_data = {
            "blockNumber": str(transfer.block_number),
            "timeStamp": transfer.block_timestamp.strftime("%s"),
            "hash": bytes_to_hex_str(transfer.transaction_hash),
            "nonce": str(nonce),
            "blockHash": bytes_to_hex_str(transfer.block_hash),
            "contractAddress": transfer.token_address,
            "from": bytes_to_hex_str(transfer.from_address),
            "to": bytes_to_hex_str(transfer.to_address),
            "tokenName": token_info.name if token_info else "",
            "tokenSymbol": token_info.symbol if token_info else "",
            "transactionIndex": str(transaction_index),
            "gas": str(gas),
            "gasPrice": str(gas_price),
            "gasUsed": str(receipt_gas_used),
            "cumulativeGasUsed": str(receipt_cumulative_gas_used),
        }
        if token_type == "ERC20":
            transfer_data["value"] = str(transfer.value)
            transfer_data["tokenDecimal"] = str(token_info.decimals) if token_info else ""
        elif token_type == "ERC721":
            transfer_data["tokenID"] = str(transfer.token_id)
        elif token_type == "ERC1155":
            transfer_data["tokenValue"] = str(transfer.value)
            transfer_data["tokenID"] = str(transfer.token_id)
        result.append(transfer_data)
    return result


def token_holder_list(session: Session, contract_address: str, token_type: str) -> List[dict]:
    token = session.exec(select(Tokens).where(Tokens.address == contract_address)).first()
    if token is None:
        return []
    stmt = (
        select(CurrentTokenBalances.address, func.sum(CurrentTokenBalances.balance).label("balance"))
        .where(and_(CurrentTokenBalances.address == contract_address, CurrentTokenBalances.balance > 0))
        .group_by(CurrentTokenBalances.address)
        .order_by(func.sum(CurrentTokenBalances.balance).desc())
        .limit(10000)
    )
    holders = session.exec(stmt).all()
    return [{"TokenHolderAddress": holder[0], "TokenHolderQuantity": str(holder[1])} for holder in holders]


@router.get("/v1/explorer/export/token_transfers")
async def export_erc20_token_transfers(
    session: ReadSessionDep,
    block_range: Tuple[int, int] = Depends(get_block_range),
    contractaddress: Optional[str] = Query(None, description="Contract address"),
    address: Optional[str] = Query(None, description="Wallet address"),
):
    start_block_number, end_block_number = block_range
    header = [
        "blockNumber",
        "timeStamp",
        "hash",
        "nonce",
        "blockHash",
        "contractAddress",
        "from",
        "to",
        "tokenName",
        "tokenSymbol",
        "transactionIndex",
        "gas",
        "gasPrice",
        "gasUsed",
        "cumulativeGasUsed",
        "value",
        "tokenDecimal",
    ]
    result = token_transfers(session, contractaddress, address, start_block_number, end_block_number, "ERC20")
    filename = f"erc20_token_transfers-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/nft_token_transfers")
async def export_erc721_token_transfers(
    session: ReadSessionDep,
    block_range: Tuple[int, int] = Depends(get_block_range),
    contractaddress: Optional[str] = Query(None, description="Contract address"),
    address: Optional[str] = Query(None, description="Wallet address"),
):
    start_block_number, end_block_number = block_range
    header = [
        "blockNumber",
        "timeStamp",
        "hash",
        "nonce",
        "blockHash",
        "contractAddress",
        "from",
        "to",
        "tokenName",
        "tokenSymbol",
        "transactionIndex",
        "gas",
        "gasPrice",
        "gasUsed",
        "cumulativeGasUsed",
        "tokenID",
    ]
    result = token_transfers(session, contractaddress, address, start_block_number, end_block_number, "ERC721")
    filename = f"erc721_token_transfers-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/nft1155_token_transfers")
async def export_erc1155_token_transfers(
    session: ReadSessionDep,
    block_range: Tuple[int, int] = Depends(get_block_range),
    contractaddress: Optional[str] = Query(None, description="Contract address"),
    address: Optional[str] = Query(None, description="Wallet address"),
):
    start_block_number, end_block_number = block_range
    header = [
        "blockNumber",
        "timeStamp",
        "hash",
        "nonce",
        "blockHash",
        "contractAddress",
        "from",
        "to",
        "tokenName",
        "tokenSymbol",
        "transactionIndex",
        "gas",
        "gasPrice",
        "gasUsed",
        "cumulativeGasUsed",
        "tokenValue",
        "tokenID",
    ]
    result = token_transfers(session, contractaddress, address, start_block_number, end_block_number, "ERC1155")
    filename = f"erc1155_token_transfers-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/token_holders/{contract_address}")
async def export_erc20_token_holders(
    session: ReadSessionDep, contract_address: str = Path(..., description="Contract address")
):
    header = ["TokenHolderAddress", "TokenHolderQuantity"]
    result = token_holder_list(session, contract_address, "ERC20")
    filename = f"erc20_token_holders-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/nft_token_holders/{contract_address}")
async def export_erc721_token_holders(
    session: ReadSessionDep, contract_address: str = Path(..., description="Contract address")
):
    header = ["TokenHolderAddress", "TokenHolderQuantity"]
    result = token_holder_list(session, contract_address, "ERC721")
    filename = f"erc721_token_holders-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)


@router.get("/v1/explorer/export/nft1155_token_holders/{contract_address}")
async def export_erc1155_token_holders(
    session: ReadSessionDep, contract_address: str = Path(..., description="Contract address")
):
    header = ["TokenHolderAddress", "TokenHolderQuantity"]
    result = token_holder_list(session, contract_address, "ERC1155")
    filename = f"erc1155_token_holders-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return response_csv(result, filename, header)
