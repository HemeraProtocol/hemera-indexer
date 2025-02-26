#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/20 15:01
# @Author  ideal93
# @File  transaction.py
# @Brief
from datetime import datetime, timedelta
from typing import Annotated, Any, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlmodel import and_, desc, func, select

from hemera.app.api.deps import ReadSessionDep
from hemera.app.api.routes.enricher import BlockchainEnricherDep
from hemera.app.api.routes.enricher.address_enricher import Address, EnricherType
from hemera.app.api.routes.explorer.token import TokenTransferItem, TokenTransferResponse
from hemera.app.api.routes.helper.internal_transaction import (
    InternalTransactionAbbr,
    get_internal_transactions,
    get_internal_transactions_by_address,
    get_internal_transactions_by_block_number,
    get_internal_transactions_by_hash,
    get_internal_transactions_count,
    get_internal_transactions_count_by_address,
    get_internal_transactions_count_by_block_number,
)
from hemera.app.api.routes.helper.log import LogItem, get_logs_by_hash
from hemera.app.api.routes.helper.token_transfers import get_token_transfers_by_hash
from hemera.app.api.routes.helper.transaction import (
    TransactionAbbr,
    TransactionDetail,
    get_transactions_and_total_count_by_condition,
    get_transactions_by_address,
    get_transactions_count_by_address,
)
from hemera.app.core.config import settings
from hemera.common.models.blocks import Blocks
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.common.utils.web3_utils import valid_hash

router = APIRouter(tags=["TRANSACTION"])


class InternalTransactionItem(InternalTransactionAbbr):
    from_addr: Address
    to_addr: Address
    display_value: str


class InternalTransactionResponse(BaseModel):
    data: List[InternalTransactionItem]
    total: int
    max_display: Optional[int] = None
    page: Optional[int] = None
    size: Optional[int] = None


class TransactionItem(TransactionAbbr):
    from_addr: Address
    to_addr: Address
    display_value: str
    value_usd: Optional[str]
    transaction_fee_usd: Optional[str]


class TransactionResponse(BaseModel):
    data: List[TransactionItem]
    total: int
    max_display: int
    page: int
    size: int


class LogResponse(BaseModel):
    total: int
    data: List[LogItem]


class TraceItem(BaseModel):
    from_address: str
    to_address: str
    value: Optional[str]
    input: Optional[str]
    output: Optional[str]
    trace_type: str
    call_type: Optional[str]
    gas: Optional[int]
    gas_used: Optional[int]
    error: Optional[str]
    status: Optional[int]
    function_name: Optional[str]
    function_input: Optional[List[dict]]
    function_output: Optional[List[dict]]
    calls: Optional[List["TraceItem"]]

    from_addr: Address
    to_addr: Address


class TransactionTracesResponse(BaseModel):
    data: TraceItem


class TransactionTraceJsonResponse(BaseModel):
    data: dict[str, Any]


@router.get("/v1/explorer/internal_transactions", response_model=InternalTransactionResponse)
async def api_get_internal_transactions(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
    address: Optional[str] = None,
    block: Optional[int] = None,
):
    if page * size > settings.MAX_INTERNAL_TRANSACTION:
        raise HTTPException(
            status_code=400,
            detail=f"Showing the last {settings.MAX_INTERNAL_TRANSACTION} records only",
        )

    offset = (page - 1) * size

    if address:
        total_count = get_internal_transactions_count_by_address(session, address, block)
        transactions = get_internal_transactions_by_address(session, address, block, limit=size, offset=offset)
    elif block:
        total_count = get_internal_transactions_count_by_block_number(session, block)
        transactions = get_internal_transactions_by_block_number(session, block, limit=size, offset=offset)
    else:
        total_count = get_internal_transactions_count(session)
        transactions = get_internal_transactions(session, limit=size, offset=offset)

    enriched_transactions = enricher.enrich(
        [transaction.dict() for transaction in transactions],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.COIN_VALUE: {"value": "display_value"},
        },
        session,
    )
    data = [InternalTransactionItem(**tx) for tx in enriched_transactions]

    return InternalTransactionResponse(
        data=data,
        total=total_count,
        max_display=min(total_count, settings.MAX_INTERNAL_TRANSACTION),
        page=page,
        size=size,
    )


class TransactionFilterParams:
    def __init__(
        self,
        block: Optional[str] = Query(None, description="Block number or hash"),
        address: Optional[str] = Query(None, description="Filter by address"),
        date: Optional[str] = Query(None, description="Filter by date (format: YYYYMMDD)"),
    ):
        self.block = block
        self.address = address
        self.date = date
        self._validate_filters()

    def _validate_filters(self):
        filter_count = sum(x is not None for x in [self.block, self.address, self.date])

        if filter_count > 1:
            raise HTTPException(status_code=400, detail="Only one filter can be applied: block, address, or date")

        if self.date:
            try:
                datetime.strptime(self.date, "%Y%m%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")

        if self.block:
            if not self.block.isnumeric() and not valid_hash(self.block):
                raise HTTPException(status_code=400, detail="Invalid block identifier")


@router.get("/v1/explorer/transactions", response_model=TransactionResponse)
async def get_transactions(
    session: ReadSessionDep,
    enricher: BlockchainEnricherDep,
    page: int = Query(1, gt=0),
    size: int = Query(25, gt=0),
    filters: TransactionFilterParams = Depends(),
):
    """Get transactions list with various filters and pagination.

    Args:
        session: Database session
        page: Page number, starting from 1
        size: Items per page
        filters: Transaction filters (block, address, or date)

    Returns:
        TransactionResponse: Paginated transaction list with metadata

    Raises:
        HTTPException: If page*size exceeds limits or invalid parameters
    """
    # Check pagination limits
    max_limit = (
        settings.MAX_TRANSACTION_WITH_CONDITION
        if any([filters.block, filters.address, filters.date])
        else settings.MAX_TRANSACTION
    )
    if page * size > max_limit:
        raise HTTPException(status_code=400, detail=f"Showing the last {max_limit} records only")

    if filters.block:
        total_records, transactions = _get_transactions_by_block(session, filters.block, page, size)
    elif filters.address:
        total_records, transactions = _get_transactions_by_address(session, filters.address, page, size)
    elif filters.date:
        total_records, transactions = _get_transactions_by_date(session, filters.date, page, size)
    else:
        # Get all transactions with pagination
        transaction_list = session.exec(
            select(Transactions)
            .order_by(desc(Transactions.block_number), desc(Transactions.transaction_index))
            .offset((page - 1) * size)
            .limit(size)
        ).all()

        total_records = _calculate_total_records(session, transaction_list, page, size)
        transactions = [TransactionAbbr.from_db_model(tx) for tx in transaction_list]

    enriched_transactions = enricher.enrich(
        [transaction.dict() for transaction in transactions],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.COIN_VALUE: {"value": "display_value"},
            EnricherType.COIN_PRICE: {"transaction_fee": "transaction_fee_usd", "display_value": "value_usd"},
        },
        session,
    )

    return TransactionResponse(
        data=[TransactionItem(**tx) for tx in enriched_transactions],
        total=total_records,
        max_display=min(max_limit, total_records),
        page=page,
        size=size,
    )


def _get_transactions_by_block(
    session: ReadSessionDep, block: str, page: int, size: int
) -> Tuple[int, List[TransactionAbbr]]:
    """Get transactions by block number or hash

    Args:
        session: Database session
        block: Block number or hash
        page: Page number
        size: Items per page

    Returns:
        Tuple[int, List[TransactionAbbr]]: Total count and list of transactions
    """
    if block.isnumeric():
        # Query by block number
        block_number = int(block)
        chain_block = session.exec(select(Blocks).where(Blocks.number == block_number)).first()
        if not chain_block:
            raise HTTPException(status_code=400, detail="Block not exist")

        transactions = session.exec(
            select(Transactions)
            .where(Transactions.block_number == block_number)
            .order_by(Transactions.block_number.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()

        return chain_block.transactions_count, [TransactionAbbr.from_db_model(tx) for tx in transactions]
    else:
        # Query by block hash
        block_hash = hex_str_to_bytes(block)
        chain_block = session.exec(select(Blocks).where(Blocks.hash == block_hash)).first()
        if not chain_block:
            raise HTTPException(status_code=400, detail="Block not exist")

        transactions = session.exec(
            select(Transactions)
            .where(Transactions.block_hash == block_hash)
            .order_by(Transactions.block_number.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()

        return chain_block.transactions_count, [TransactionAbbr.from_db_model(tx) for tx in transactions]


def _get_transactions_by_address(
    session: ReadSessionDep, address: str, page: int, size: int
) -> Tuple[int, List[TransactionAbbr]]:
    """Get transactions by address

    Args:
        session: Database session
        address: Address to filter by
        page: Page number
        size: Items per page

    Returns:
        Tuple[int, List[TransactionAbbr]]: Total count and list of transactions
    """
    return (
        get_transactions_count_by_address(session, address, use_address_index=True),
        get_transactions_by_address(session, address, use_address_index=True, limit=size, offset=(page - 1) * size),
    )


def _get_transactions_by_date(
    session: ReadSessionDep, date: str, page: int, size: int
) -> Tuple[int, List[Transactions]]:
    """Get transactions by date

    Args:
        session: Database session
        date: Date in YYYYMMDD format
        page: Page number
        size: Items per page

    Returns:
        Tuple[int, List[Transactions]]: Total count and list of transactions
    """
    date_obj = datetime.strptime(date, "%Y%m%d")
    start_time = date_obj
    end_time = start_time + timedelta(days=1)

    date_condition = and_(Transactions.block_timestamp >= start_time, Transactions.block_timestamp < end_time)
    transactions, total_count = get_transactions_and_total_count_by_condition(
        session,
        filter_condition=date_condition,
        limit=size,
        offset=(page - 1) * size,
    )
    return total_count, transactions


def _calculate_total_records(session: ReadSessionDep, transactions: List[Transactions], page: int, size: int) -> int:
    """Calculate total number of records

    Args:
        session: Database session
        transactions: List of transactions from current page
        page: Current page number
        size: Page size

    Returns:
        int: Total number of records
    """
    if len(transactions) > 0 and len(transactions) < size:
        return (page - 1) * size + len(transactions)
    return session.exec(select(func.count()).select_from(Transactions)).first()


async def verify_transaction_hash(
    tx_hash: Annotated[
        str,
        Path(
            title="Transaction Hash",
            description="Ethereum transaction hash (hex format)",
            min_length=66,
            max_length=66,
            pattern="^0x[0-9a-fA-F]{64}$",
        ),
    ]
) -> str:
    """
    Dependency for validating transaction hashes.

    Args:
        tx_hash: Transaction hash to validate

    Returns:
        str: Validated and formatted transaction hash

    Raises:
        HTTPException: If hash format is invalid
    """
    tx_hash = valid_hash(tx_hash)
    if not tx_hash:
        raise HTTPException(status_code=422, detail="Invalid transaction hash format")
    return tx_hash


TransactionHashDep = Annotated[str, Depends(verify_transaction_hash)]


@router.get("/v1/explorer/transaction/{tx_hash}", response_model=TransactionDetail)
async def get_transaction_detail(session: ReadSessionDep, tx_hash: TransactionHashDep):
    """Get detailed information about a specific transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If transaction not found or invalid hash
    """
    # Validate and format transaction hash
    # Get transaction with basic info
    pass


@router.get("/v1/explorer/transaction/{tx_hash}/logs", response_model=LogResponse)
async def get_transaction_logs(session: ReadSessionDep, tx_hash: TransactionHashDep):
    """Get all logs for a specific transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If invalid hash format or transaction not found
    """

    logs = get_logs_by_hash(session, tx_hash)
    return LogResponse(
        logs,
        total=len(logs),
    )


@router.get("/v1/explorer/transaction/{tx_hash}/token_transfers", response_model=TokenTransferResponse)
async def get_transaction_token_transfers(
    session: ReadSessionDep, enricher: BlockchainEnricherDep, tx_hash: TransactionHashDep
):
    """Get all token transfers (ERC20, ERC721, ERC1155) for a specific transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If invalid hash format
    """
    # Validate and format hash
    token_transfers = get_token_transfers_by_hash(session, tx_hash)

    enriched_token_transfers = enricher.enrich(
        [token_transfer.dict() for token_transfer in token_transfers],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.TOKEN_INFO: {"token_address": "token_info"},
            EnricherType.TOKEN_VALUE: {"value": "display_value"},
        },
        session,
    )

    return TokenTransferResponse(
        total=len(enriched_token_transfers), data=[TokenTransferItem(**item) for item in enriched_token_transfers]
    )


@router.get("/v1/explorer/transaction/{tx_hash}/internal_transactions", response_model=InternalTransactionResponse)
async def get_transaction_internal_transactions(session: ReadSessionDep, enricher: BlockchainEnricherDep, tx_hash: str):
    """Get internal transactions for a specific transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If invalid hash format
    """
    internal_transactions = get_internal_transactions_by_hash(session, tx_hash)

    enriched_transactions = enricher.enrich(
        [transaction.dict() for transaction in internal_transactions],
        {
            EnricherType.ADDRESS: {"to_address": "to_addr", "from_address": "from_addr"},
            EnricherType.COIN_VALUE: {"value": "display_value"},
        },
        session,
    )
    data = [InternalTransactionItem(**tx) for tx in enriched_transactions]

    return InternalTransactionResponse(
        data=data,
        total=len(data),
    )


@router.get("/v1/explorer/transaction/{tx_hash}/traces", response_model=TransactionTracesResponse)
async def get_transaction_traces(session: ReadSessionDep, enricher: BlockchainEnricherDep, tx_hash: str):
    """Get detailed trace information for a transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If invalid hash format or trace not found
    """
    # Validate and format hash
    pass


@router.get("/v1/explorer/transaction/{tx_hash}/trace_json", response_model=TransactionTraceJsonResponse)
async def get_transaction_traces(session: ReadSessionDep, enricher: BlockchainEnricherDep, tx_hash: str):
    """Get detailed trace information for a transaction.

    Args:
        session: Database session
        tx_hash: Transaction hash in hex format

    Raises:
        HTTPException: If invalid hash format or trace not found
    """
    # Validate and format hash
    pass
