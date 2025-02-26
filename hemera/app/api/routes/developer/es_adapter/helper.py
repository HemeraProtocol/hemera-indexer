#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/1 01:38
# @Author  ideal93
# @File  helper.py
# @Brief
import json
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field
from sqlmodel import Session, and_, or_, select

from hemera.common.enumeration.token_type import TokenType
from hemera.common.models.blocks import Blocks
from hemera.common.models.coin_balances import CoinBalances
from hemera.common.models.contracts import Contracts
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.logs import Logs
from hemera.common.models.stats.daily_addresses_stats import DailyAddressesStats
from hemera.common.models.stats.daily_blocks_stats import DailyBlocksStats
from hemera.common.models.stats.daily_transactions_stats import DailyTransactionsStats
from hemera.common.models.token_balances import AddressTokenBalances
from hemera.common.models.token_details import ERC721TokenIdDetails
from hemera.common.models.token_transfers import ERC20TokenTransfers, ERC721TokenTransfers, ERC1155TokenTransfers
from hemera.common.models.tokens import Tokens
from hemera.common.models.traces import ContractInternalTransactions, Traces
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


# Get Ether Balance for a Single Address
def account_balance(session: Session, address, tag=None) -> Optional[int]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    balance_record = (
        session.query(CoinBalances)
        .where(CoinBalances.address == address)
        .order_by(CoinBalances.block_number.desc())
        .limit(1)
        .first()
    )
    return int(balance_record.balance) if balance_record else None


class AddressBalance(BaseModel):
    address: str
    balance: int


# Get Ether Balance for Multiple Addresses in a Single Call
def account_balancemulti(session: Session, addresses, tag=None) -> List[AddressBalance]:
    results = []
    for address in addresses:
        if isinstance(address, str):
            address = hex_str_to_bytes(address)
        balance_record = (
            session.query(CoinBalances)
            .where(CoinBalances.address == address)
            .order_by(CoinBalances.block_number.desc())
            .limit(1)
            .first()
        )
        if balance_record:
            results.append(AddressBalance(address=address, balance=int(balance_record.balance)))
    return results


# Get Historical Ether Balance for a Single Address By BlockNo
def account_balancehistory(session: Session, address, blockno) -> int:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    balance_record = (
        session.query(CoinBalances)
        .where(
            CoinBalances.address == address,
            CoinBalances.block_number <= blockno,
        )
        .order_by(CoinBalances.block_number.desc())
        .limit(1)
        .first()
    )
    return int(balance_record.balance) if balance_record else 0


class TransactionData(BaseModel):
    blockNumber: str
    timeStamp: str
    hash: str
    nonce: str
    blockHash: str
    transactionIndex: str
    fromAddress: str
    toAddress: str
    value: str
    gas: str
    gasPrice: str
    isError: str
    txreceipt_status: str
    input: str
    contractAddress: Optional[str]
    cumulativeGasUsed: str
    gasUsed: str
    confirmations: str  # TODO:
    methodId: str
    functionName: str  # TODO: methodId


# (P0)Get a list of 'Normal' Transactions By Address
# (P0)Get 'Normal Transactions' by Transaction Hash
# (P0)Get "Normal Transactions" by Block Range
def account_txlist(
    session: Session,
    txhash: Optional[str],
    address: Optional[str],
    start_block: int,
    end_block: int,
    page: int,
    offset: int,
    sort_order: str,
) -> List[TransactionData]:
    if txhash:
        query = session.query(Transactions).filter_by(hash=hex_str_to_bytes(txhash))
    else:
        query = session.query(Transactions).where(
            and_(Transactions.block_number >= start_block, Transactions.block_number <= end_block)
        )

        if address:
            condition = or_(
                Transactions.from_address == hex_str_to_bytes(address),
                Transactions.to_address == hex_str_to_bytes(address),
            )
            query = query.where(condition)

    if sort_order == "asc":
        query = query.order_by(Transactions.block_number.asc())
    else:
        query = query.order_by(Transactions.block_number.desc())

    transactions = query.limit(offset).offset((page - 1) * offset).all()

    return [
        TransactionData(
            blockNumber=str(tx.block_number),
            timeStamp=tx.block_timestamp.strftime("%s"),
            hash=bytes_to_hex_str(tx.hash),
            nonce=str(tx.nonce),
            blockHash=bytes_to_hex_str(tx.block_hash),
            transactionIndex=str(tx.transaction_index),
            fromAddress=bytes_to_hex_str(tx.from_address),
            toAddress=bytes_to_hex_str(tx.to_address),
            value=str(tx.value),
            gas=str(tx.gas),
            gasPrice=str(tx.gas_price),
            isError="0" if tx.receipt_status == 1 else "1",
            txreceipt_status=str(tx.receipt_status),
            input=bytes_to_hex_str(tx.input) or "",
            contractAddress=bytes_to_hex_str(tx.receipt_contract_address),
            cumulativeGasUsed=str(tx.receipt_cumulative_gas_used),
            gasUsed=str(tx.receipt_gas_used),
            confirmations="",  #
            methodId=bytes_to_hex_str(tx.input)[0:10] if tx.input else "",
            functionName="",  #
        )
        for tx in transactions
    ]


class TransactionInternalData(BaseModel):
    blockNumber: str
    timeStamp: str
    hash: str
    fromAddress: str
    toAddress: str
    value: str
    contractAddress: Optional[str]
    input: str
    type: str
    gas: str
    gasUsed: str
    traceId: str
    isError: str
    errCode: Optional[int]


# (P0)Get a list of 'Internal' Transactions by Address
# (P0)Get 'Internal Transactions' by Transaction Hash
# (P0)Get "Internal Transactions" by Block Range
def account_txlistinternal(
    session: Session,
    txhash: Optional[str],
    address: Optional[str],
    start_block: int,
    end_block: int,
    page: int,
    offset: int,
    sort_order: str,
) -> List[TransactionInternalData]:
    if txhash:
        query = session.query(ContractInternalTransactions).filter_by(transaction_hash=hex_str_to_bytes(txhash))
    else:
        query = session.query(ContractInternalTransactions).where(
            and_(
                ContractInternalTransactions.block_number >= start_block,
                ContractInternalTransactions.block_number <= end_block,
            ),
        )

        if address:
            condition = or_(
                ContractInternalTransactions.from_address == hex_str_to_bytes(address),
                ContractInternalTransactions.to_address == hex_str_to_bytes(address),
            )
            query = query.where(condition)

    query = query.order_by(
        ContractInternalTransactions.block_number.asc()
        if sort_order == "asc"
        else ContractInternalTransactions.block_number.desc()
    )

    internal_transactions = query.limit(offset).offset((page - 1) * offset).all()

    return [
        TransactionInternalData(
            blockNumber=str(tx.block_number),
            timeStamp=tx.block_timestamp.strftime("%s"),
            hash=bytes_to_hex_str(tx.transaction_hash),
            fromAddress=bytes_to_hex_str(tx.from_address),
            toAddress=bytes_to_hex_str(tx.to_address),
            value=str(tx.value),
            contractAddress=bytes_to_hex_str(tx.to_address) if tx.trace_type in ["create", "create2"] else "",
            input=bytes_to_hex_str(tx.input) or "",  # TODO
            type=tx.trace_type,
            gas=str(tx.gas),
            gasUsed=str(tx.gas_used),
            traceId=tx.trace_id,
            isError="1" if tx.error == 0 else "0",
            errCode=tx.error,
        )
        for tx in internal_transactions
    ]


# (P0)Get a list of 'ERC20 - Token Transfer Events' by Address
# (P0)Get a list of 'ERC721 - Token Transfer Events' by Address
# (P0)Get a list of 'ERC1155 - Token Transfer Events' by Address


class TokenTransferBase(BaseModel):
    block_number: str = Field(alias="blockNumber")
    time_stamp: str = Field(alias="timeStamp")
    hash: str
    nonce: str
    block_hash: str = Field(alias="blockHash")
    from_address: str = Field(alias="from")
    contract_address: str = Field(alias="contractAddress")
    to: str
    token_name: str = Field(alias="tokenName")
    token_symbol: str = Field(alias="tokenSymbol")
    transaction_index: str = Field(alias="transactionIndex")
    gas: str
    gas_price: str = Field(alias="gasPrice")
    gas_used: str = Field(alias="gasUsed")
    cumulative_gas_used: str = Field(alias="cumulativeGasUsed")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class ERC20Transfer(TokenTransferBase):
    value: str
    token_decimal: str = Field(alias="tokenDecimal")


class ERC721Transfer(TokenTransferBase):
    token_id: str = Field(alias="tokenID")


class ERC1155Transfer(TokenTransferBase):
    token_value: str = Field(alias="tokenValue")
    token_id: str = Field(alias="tokenID")


def get_account_token_transfers(
    session: Session,
    contract_address: Optional[str] = None,
    address: Optional[str] = None,
    page: int = 1,
    offset: int = 10,
    sort_order: str = "desc",
    start_block: int = 0,
    end_block: int = 99999999,
    token_type: TokenType = TokenType.ERC20,
) -> List[Union[ERC20Transfer, ERC721Transfer, ERC1155Transfer]]:
    # Input validation
    if address is None and contract_address is None:
        return []
    if token_type not in [TokenType.ERC20, TokenType.ERC721, TokenType.ERC1155]:
        token_type = TokenType.ERC20
    transfer_model = {
        TokenType.ERC20: ERC20TokenTransfers,
        TokenType.ERC721: ERC721TokenTransfers,
        TokenType.ERC1155: ERC1155TokenTransfers,
    }[token_type]
    response_model = {
        TokenType.ERC20: ERC20Transfer,
        TokenType.ERC721: ERC721Transfer,
        TokenType.ERC1155: ERC1155Transfer,
    }[token_type]

    # Build conditions
    conditions = []
    if contract_address:
        conditions.append(transfer_model.token_address == hex_str_to_bytes(contract_address))
    if address:
        conditions.append(
            or_(
                transfer_model.from_address == hex_str_to_bytes(address),
                transfer_model.to_address == hex_str_to_bytes(address),
            )
        )
    conditions.extend([transfer_model.block_number >= start_block, transfer_model.block_number <= end_block])

    query = (
        select(transfer_model, Transactions)
        .where(and_(*conditions))
        .join(Transactions, transfer_model.transaction_hash == Transactions.hash)
        .order_by(transfer_model.block_number.desc() if sort_order == "desc" else transfer_model.block_number.asc())
        .offset((page - 1) * offset)
        .limit(offset)
    )

    # Execute query
    transfers = session.exec(query).all()

    if not transfers:
        return []

    # Get tokens info
    token_addresses = {transfer.token_address for transfer, _ in transfers}
    tokens = session.exec(select(Tokens).where(Tokens.address.in_(token_addresses))).all()
    token_dict = {token.address: token for token in tokens}

    # Format results
    result = []
    for transfer, tx in transfers:
        base_data = {
            "blockNumber": str(transfer.block_number),
            "timeStamp": transfer.block_timestamp.strftime("%s"),
            "hash": bytes_to_hex_str(transfer.transaction_hash) or "",
            "nonce": str(tx.nonce),
            "blockHash": bytes_to_hex_str(transfer.block_hash),
            "from": bytes_to_hex_str(transfer.from_address),
            "contractAddress": bytes_to_hex_str(transfer.token_address),
            "to": bytes_to_hex_str(transfer.to_address),
            "tokenName": token_dict[transfer.token_address].name,
            "tokenSymbol": token_dict[transfer.token_address].symbol,
            "transactionIndex": str(tx.transaction_index),
            "gas": str(tx.gas),
            "gasPrice": str(tx.gas_price),
            "gasUsed": str(tx.receipt_gas_used),
            "cumulativeGasUsed": str(tx.receipt_cumulative_gas_used),
        }

        # Add token type specific fields
        if token_type == TokenType.ERC20:
            base_data["value"] = str(transfer.value)
            base_data["tokenDecimal"] = str(token_dict[transfer.token_address].decimals)
        elif token_type == TokenType.ERC721:
            base_data["tokenID"] = str(transfer.token_id)
        elif token_type == TokenType.ERC1155:
            base_data["tokenValue"] = str(transfer.value)
            base_data["tokenID"] = str(transfer.token_id)

        result.append(response_model(**base_data))

    return result


# Check Contract Execution Status
class ContractExecutionStatus(BaseModel):
    isError: str
    errDescription: Optional[str]


def check_contract_execution_status(session: Session, txn_hash: str) -> Optional[ContractExecutionStatus]:
    transaction = (
        session.exec(
            select(Traces.status, Traces.error).where(
                Traces.transaction_hash == hex_str_to_bytes(txn_hash),
                Traces.trace_address == "{}",
            )
        )
    ).first()

    if transaction:
        return ContractExecutionStatus(
            isError="1" if transaction.status == 0 else "0",
            errDescription=transaction.error if transaction.status == 0 else "",
        )
    else:
        return None


class TransactionReceiptStatus(BaseModel):
    status: str


# Check Transaction Receipt Status
def check_transaction_receipt_status(session: Session, txn_hash: str) -> Optional[TransactionReceiptStatus]:
    receipt_status = (
        session.exec(
            select(Transactions.receipt_status).where(
                Transactions.hash == hex_str_to_bytes(txn_hash),
            )
        )
    ).first()
    if receipt_status:
        return TransactionReceiptStatus(status=str(receipt_status))
    else:
        return None


# (P0)Get Event Logs by Address
# (P0)Get Event Logs by Topics
# (P0)Get Event Logs by Address filtered by Topics


class APILogResponse(BaseModel):
    transactionHash: str
    logIndex: str
    address: str
    data: str
    blockNumber: str
    timeStamp: str
    topics: List[str]


def get_event_logs(
    session: Session,
    topic0: Optional[str] = None,
    topic1: Optional[str] = None,
    topic2: Optional[str] = None,
    topic3: Optional[str] = None,
    topic0_1_opr: str = "and",
    topic1_2_opr: str = "and",
    topic2_3_opr: str = "and",
    topic0_2_opr: str = "and",
    topic1_3_opr: str = "and",
    topic0_3_opr: str = "and",
    address: Optional[str] = None,
    from_block: int = 0,
    to_block: int = 999999999,
    page: int = 1,
    offset: int = 10,
    sort_order: str = "desc",
) -> List[APILogResponse]:
    conditions = []

    if topic0:
        conditions.append(("topic0", Logs.topic0 == hex_str_to_bytes(topic0)))
    if topic1:
        conditions.append(("topic1", Logs.topic1 == hex_str_to_bytes(topic1)))
    if topic2:
        conditions.append(("topic2", Logs.topic2 == hex_str_to_bytes(topic2)))
    if topic3:
        conditions.append(("topic3", Logs.topic3 == hex_str_to_bytes(topic3)))

    opr_funcs = {"and": and_, "or": or_}

    def get_operator(opr_key: str, default_opr: str = "and"):
        return opr_funcs.get(opr_key, opr_funcs[default_opr])

    opr_mapping = {
        ("topic0", "topic1"): topic0_1_opr,
        ("topic1", "topic2"): topic1_2_opr,
        ("topic2", "topic3"): topic2_3_opr,
        ("topic0", "topic2"): topic0_2_opr,
        ("topic1", "topic3"): topic1_3_opr,
        ("topic0", "topic3"): topic0_3_opr,
    }

    # Build the final condition
    final_condition = True
    if conditions:
        final_condition = conditions[0][1]
        for i in range(1, len(conditions)):
            prev_topic, current_topic = conditions[i - 1][0], conditions[i][0]
            opr_key = opr_mapping.get((prev_topic, current_topic), "and")
            opr_func = get_operator(opr_key)
            final_condition = opr_func(final_condition, conditions[i][1])

    if address:
        final_condition = and_(final_condition, Logs.address == hex_str_to_bytes(address))

    # Build and execute query
    query = select(Logs).where(final_condition, Logs.block_number >= from_block, Logs.block_number <= to_block)

    if sort_order == "asc":
        query = query.order_by(Logs.block_number.asc())
    else:
        query = query.order_by(Logs.block_number.desc())

    query = query.offset((page - 1) * offset).limit(offset)
    logs = session.exec(query).all()

    # Format results
    result = [
        APILogResponse(
            transactionHash=bytes_to_hex_str(log.transaction_hash) or "",
            logIndex=str(log.log_index),
            address=bytes_to_hex_str(log.address) or "",
            data=bytes_to_hex_str(log.data) or "",
            blockNumber=str(log.block_number),
            timeStamp=log.block_timestamp.strftime("%s"),
            topics=[
                topic
                for topic in [
                    bytes_to_hex_str(log.topic0),
                    bytes_to_hex_str(log.topic1),
                    bytes_to_hex_str(log.topic2),
                    bytes_to_hex_str(log.topic3),
                ]
                if topic is not None
            ],
        )
        for log in logs
    ]

    return result


# (P0)Get ERC20-Token TotalSupply by ContractAddress
# (P0)Get ERC721-Token TotalSupply by ContractAddress
# (P0)Get ERC1155-Token TotalSupply by ContractAddress
def stats_token_supply(session: Session, contract_address: str) -> Optional[int]:
    total_supply = session.exec(
        select(Tokens.total_supply).where(Tokens.address == hex_str_to_bytes(contract_address))
    ).first()

    if not total_supply:
        return None
    else:
        return int(total_supply)


# Get ERC20-Token Account Balance for TokenContractAddress
# Get ERC721-Token Account Balance for TokenContractAddress
# Get ERC1155-Token Account Balance for TokenContractAddress
def account_token_balance(
    session: Session, contract_address: str, address: str, token_type: TokenType = TokenType.ERC20, token_id: int = -1
) -> Optional[str]:
    if not address or not contract_address:
        return "0"

    token_balance = session.exec(
        select(CurrentTokenBalances.balance).where(
            CurrentTokenBalances.address == hex_str_to_bytes(address),
            CurrentTokenBalances.token_address == hex_str_to_bytes(contract_address),
            CurrentTokenBalances.token_type == token_type.value,
            CurrentTokenBalances.token_id == token_id,
        )
    ).first()

    return str(token_balance or 0)


# Get Historical ERC20-Token Account Balance for TokenContractAddress by BlockNo
# Get Historical ERC721-Token Account Balance for TokenContractAddress by BlockNo
# Get Historical ERC1155-Token Account Balance for TokenContractAddress by BlockNo
def account_token_balance_with_block_number(
    session: Session, contract_address: str, address: str, block_number: int, token_type: str, token_id: int = -1
) -> str:
    if not address or not contract_address or not block_number:
        return "0"

    token_balance = session.exec(
        select(AddressTokenBalances.balance)
        .where(
            and_(
                AddressTokenBalances.address == hex_str_to_bytes(address),
                AddressTokenBalances.token_address == hex_str_to_bytes(contract_address),
                AddressTokenBalances.token_type == token_type,
                AddressTokenBalances.token_id == token_id,
                AddressTokenBalances.block_number <= block_number,
            )
        )
        .order_by(AddressTokenBalances.block_number.desc())
    ).first()

    return str(token_balance or 0)


class TokenHolderResponse(BaseModel):
    TokenHolderAddress: str
    TokenId: Optional[str]
    TokenHolderQuantity: str


# (P0)Get Token Holder List by Contract Address
def token_holder_list(
    session: Session, contract_address: str, page: int, offset: int, sort_order: str
) -> Optional[List[TokenHolderResponse]]:
    token = session.exec(select(Tokens).where(Tokens.address == hex_str_to_bytes(contract_address))).first()

    if token is None:
        return None

    query = select(CurrentTokenBalances).where(CurrentTokenBalances.token_address == hex_str_to_bytes(contract_address))

    if sort_order == "asc":
        query = query.order_by(CurrentTokenBalances.balance.asc())
    else:
        query = query.order_by(CurrentTokenBalances.balance.desc())

    query = query.offset((page - 1) * offset).limit(offset)
    token_holders = session.exec(query).all()

    return [
        TokenHolderResponse(
            TokenHolderAddress=bytes_to_hex_str(token_holder.address),
            TokenId=token_holder.token_id if token_holder.token_id >= 0 else None,
            TokenHolderQuantity=str(token_holder.balance),
        )
        for token_holder in token_holders
    ]


class TokenInfoResponse(BaseModel):
    TokenName: str
    TokenSymbol: str
    TokenTotalSupply: str
    TokenType: str
    TokenDecimals: Optional[str] = None


# Get Token Info by ContractAddress
def token_info(session: Session, contract_address: str) -> Optional[TokenInfoResponse]:
    query = select(Tokens).where(Tokens.address == hex_str_to_bytes(contract_address))
    token = session.exec(query).first()

    if token:
        return TokenInfoResponse(
            TokenName=token.name,
            TokenSymbol=token.symbol,
            TokenTotalSupply=str(token.total_supply),
            TokenType=token.token_type,
            TokenDecimals=str(token.decimals) if token.decimals else None,
        )
    else:
        return None


class NftInventory(BaseModel):
    tokenID: str


# Get Address ERC721 Token Inventory By Contract Address
def account_address_nft_inventory(session: Session, contract_address, address, page, offset) -> List[NftInventory]:
    if not address or not contract_address:
        return []
    address = address.lower()
    contract_address = contract_address.lower()
    query = (
        select(ERC721TokenIdDetails)
        .where(
            ERC721TokenIdDetails.token_address == hex_str_to_bytes(contract_address),
            ERC721TokenIdDetails.token_owner == hex_str_to_bytes(address),
        )
        .order_by(ERC721TokenIdDetails.token_id.asc())
        .limit(offset)
        .offset((page - 1) * offset)
    )
    result = session.exec(query)
    result = [
        NftInventory(
            tokenID=str(token.token_id),
        )
        for token in result
    ]
    return result


# Get Contract Creator and Creation Tx Hash
class ContractInfo(BaseModel):
    contractAddress: str
    contractCreator: str
    txHash: str


def get_contract_creator_and_creation_tx_hash(session: Session, contract_addresses) -> List[ContractInfo]:
    if not contract_addresses:
        return []
    contract_addresses = [hex_str_to_bytes(address) for address in contract_addresses]
    query = select(Contracts).where(Contracts.address.in_(contract_addresses))
    contracts = session.exec(query).all()
    result = [
        ContractInfo(
            contractAddress=bytes_to_hex_str(contract.address),
            contractCreator=bytes_to_hex_str(contract.contract_creator),
            txHash=bytes_to_hex_str(contract.transaction_hash),
        )
        for contract in contracts
    ]
    return result


# (P0)Get Address ERC20 Token Holding
# (P0)Get Address ERC721 Token Holding
# (P0)Get Address ERC1155 Token Holding


class AddressTokenQuantity(BaseModel):
    TokenAddress: str
    TokenName: str
    TokenType: str
    TokenSymbol: str
    TokenQuantity: str

    TokenDecimals: Optional[str]
    TokenID: Optional[str]


def account_address_token_holding(
    session: Session, address: str, page: int, offset: int, token_type: Optional[TokenType] = None
) -> List[AddressTokenQuantity]:
    if address is None:
        return []
    # Main query with joins
    query = (
        select(
            CurrentTokenBalances.token_address,
            CurrentTokenBalances.balance,
            CurrentTokenBalances.token_id,
            Tokens.name,
            Tokens.token_type,
            Tokens.symbol,
            Tokens.icon_url,
            Tokens.decimals,
        )
        .outerjoin(
            Tokens,
            and_(
                CurrentTokenBalances.token_address == Tokens.address,
            ),
        )
        .order_by(CurrentTokenBalances.token_address.asc())
    )
    query = query.where(CurrentTokenBalances.address == hex_str_to_bytes(address))
    if token_type:
        query = query.where(Tokens.token_type == token_type.value)
    result = session.exec(query.offset((page - 1) * offset).limit(offset)).all()

    token_holder_list = []
    for token_holder in result:
        token_holder_list.append(
            AddressTokenQuantity(
                TokenAddress=bytes_to_hex_str(token_holder.token_address),
                TokenName=token_holder.name or "Unknown Token",
                TokenType=token_holder.token_type,
                TokenSymbol=token_holder.symbol or "UNKNOWN",
                # TokenQuantity=str(token_holder.balance / (10**token_holder.decimals or 0)),
                TokenQuantity=str(token_holder.balance or 0),
                TokenDecimals=str(token_holder.decimals) if token_holder.decimals else None,
                TokenID=str(token_holder.token_id) if token_holder.token_id >= 0 else None,
            )
        )
    return token_holder_list


# Get Block Number by Timestamp
def block_number_by_timestamp(session: Session, timestamp: int, closest) -> Optional[int]:
    if closest == "before":
        block_number = session.exec(
            select(Blocks.number)
            .where(Blocks.timestamp <= datetime.fromtimestamp(timestamp))
            .order_by(Blocks.number.desc())
            .limit(1)
        ).first()
    elif closest == "after":
        block_number = session.exec(
            select(Blocks.number)
            .where(Blocks.timestamp >= datetime.fromtimestamp(timestamp))
            .order_by(Blocks.number.asc())
            .limit(1)
        ).first()
    else:
        return None
    return block_number


# Get Daily Network Transaction Fee
class DailyTransactionFeeResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    transactionFee: str


def stats_daily_network_transaction_fee(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyTransactionFeeResponse]:
    query = select(
        DailyTransactionsStats.block_date,
        DailyTransactionsStats.avg_transaction_fee,
    ).where(and_(DailyTransactionsStats.block_date >= start_date, DailyTransactionsStats.block_date <= end_date))

    if sort_order == "asc":
        query = query.order_by(DailyTransactionsStats.block_date.asc())
    else:
        query = query.order_by(DailyTransactionsStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyTransactionFeeResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            transactionFee=str(row.avg_transaction_fee),
        )
        for row in results
    ]


# Get Daily New Address Count


class DailyNewAddressCountResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    newAddressCount: str


def stats_daily_new_address_count(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyNewAddressCountResponse]:
    query = select(
        DailyAddressesStats.block_date,
        DailyAddressesStats.new_address_cnt,
    ).where(DailyAddressesStats.block_date >= start_date, DailyAddressesStats.block_date <= end_date)

    if sort_order == "asc":
        query = query.order_by(DailyAddressesStats.block_date.asc())
    else:
        query = query.order_by(DailyAddressesStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyNewAddressCountResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            newAddressCount=str(row.new_address_cnt),
        )
        for row in results
    ]


# Get Daily Network Utilization
class DailyNetworkUtilizationResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    networkUtilization: str


def stats_daily_network_utilization(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyNetworkUtilizationResponse]:
    query = select(
        DailyBlocksStats.block_date,
        DailyBlocksStats.avg_gas_used_percentage,
    ).where(and_(DailyBlocksStats.block_date >= start_date, DailyBlocksStats.block_date <= end_date))

    if sort_order == "asc":
        query = query.order_by(DailyBlocksStats.block_date.asc())
    else:
        query = query.order_by(DailyBlocksStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyNetworkUtilizationResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            networkUtilization=str(row.avg_gas_used_percentage),
        )
        for row in results
    ]


# Get Daily Transaction Count
class DailyTransactionCountResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    transactionCount: str


def stats_daily_transaction_count(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyTransactionCountResponse]:
    query = select(DailyTransactionsStats.block_date, DailyTransactionsStats.cnt).where(
        DailyTransactionsStats.block_date >= start_date, DailyTransactionsStats.block_date <= end_date
    )

    if sort_order == "asc":
        query = query.order_by(DailyTransactionsStats.block_date.asc())
    else:
        query = query.order_by(DailyTransactionsStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyTransactionCountResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            transactionCount=str(row.cnt),
        )
        for row in results
    ]


class DailyAverageBlockSizeResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    averageBlockSize: str


def stats_daily_average_block_size(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyAverageBlockSizeResponse]:
    query = select(DailyBlocksStats.block_date, DailyBlocksStats.avg_size).where(
        DailyBlocksStats.block_date >= start_date, DailyBlocksStats.block_date <= end_date
    )

    if sort_order == "asc":
        query = query.order_by(DailyBlocksStats.block_date.asc())
    else:
        query = query.order_by(DailyBlocksStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyAverageBlockSizeResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            averageBlockSize=str(row.avg_size),
        )
        for row in results
    ]


# Get Daily Block Count and Rewards
class DailyBlockCountAndRewardsResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    blockCount: str


def stats_daily_block_count_and_rewards(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyBlockCountAndRewardsResponse]:
    query = select(DailyBlocksStats.block_date, DailyBlocksStats.cnt).where(
        and_(DailyBlocksStats.block_date >= start_date, DailyBlocksStats.block_date <= end_date)
    )

    if sort_order == "asc":
        query = query.order_by(DailyBlocksStats.block_date.asc())
    else:
        query = query.order_by(DailyBlocksStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyBlockCountAndRewardsResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            blockCount=str(row.cnt),
        )
        for row in results
    ]


# Get Daily Average Time for A Block to be Included in the Ethereum Blockchain
class DailyAverageBlockTimeResponse(BaseModel):
    UTCDate: str
    unixTimeStamp: str
    blockTime: str


def stats_daily_average_block_time(
    session: Session, start_date: datetime, end_date: datetime, sort_order: str
) -> List[DailyAverageBlockTimeResponse]:
    query = select(DailyBlocksStats.block_date, DailyBlocksStats.block_interval).where(
        and_(DailyBlocksStats.block_date >= start_date, DailyBlocksStats.block_date <= end_date)
    )

    if sort_order == "asc":
        query = query.order_by(DailyBlocksStats.block_date.asc())
    else:
        query = query.order_by(DailyBlocksStats.block_date.desc())

    results = session.exec(query).all()

    return [
        DailyAverageBlockTimeResponse(
            UTCDate=row.block_date.strftime("%Y-%m-%d"),
            unixTimeStamp=row.block_date.strftime("%s"),
            blockTime=str(row.block_interval),
        )
        for row in results
    ]


# Get Contract ABI for Verified Contract Source Codes
def get_contract_abi(session: Session, contract_address):
    if not contract_address:
        return None
    contract = get_contract_verification_abi_by_address(contract_address)
    if contract:
        return contract.get("abi")
    else:
        return None


class ContractInfoResponse(BaseModel):
    SourceCode: str
    ABI: str
    ContractName: str
    CompilerVersion: str
    OptimizationUsed: str
    Runs: str
    ConstructorArguments: str
    EVMVersion: str
    Library: str
    LicenseType: str
    Proxy: str
    Implementation: str


# Get Contract Source for Verified Contract Source Codes
def get_contract_source_code(session: Session, contract_address: str):
    if not contract_address:
        return None

    contract_address = contract_address.lower()

    # Query the contract from the database
    contract = session.exec(select(Contracts).where(Contracts.address == hex_str_to_bytes(contract_address))).first()

    if not contract or not contract.is_verified:
        return None

    # Fetch contract verification details
    contracts_verification = get_contract_code_by_address(address=contract_address)
    if not contracts_verification:
        return None

    source_code = {}
    code = {}

    # Check if the folder path is available for contract verification
    if "folder_path" in contracts_verification and len(contracts_verification["folder_path"]) > 0:
        if len(contracts_verification["folder_path"]) == 1:
            source_code = aws_service.get_file_content(
                "contract-verify-files", contracts_verification["folder_path"][0]
            )
        else:
            settings = json.loads(contracts_verification.get("settings", "{}"))
            source_code["settings"] = settings

            remappings = settings.get("remappings", [])
            remappings_dict = {"src/": ""}
            for remapping_str in remappings:
                remapping = remapping_str.split("=")
                if len(remapping) == 2:
                    remappings_dict[remapping[1]] = remapping[0]

            sorted_remappings = sorted(remappings_dict.items(), key=lambda x: len(x[0]), reverse=True)

            for file in contracts_verification["folder_path"]:
                content = aws_service.get_file_content("contract-verify-files", file)
                if content:
                    key = file.removeprefix(f"{CHAIN_ID}/{contract_address}/")
                    for remap_key, remap_value in sorted_remappings:
                        if key.startswith(remap_key):
                            key = key.replace(remap_key, remap_value)
                            break
                    code[key] = {"content": content}

            source_code["sources"] = code
            source_code["language"] = contracts_verification.get("language", "Solidity")

    contracts_verification["files"] = []

    # Construct the output data to return using ContractInfoResponse model
    output_data = [
        ContractInfoResponse(
            SourceCode=str(source_code),
            ABI=contracts_verification.get("abi") or "",
            ContractName=contracts_verification.get("contract_name") or "",
            CompilerVersion=contracts_verification.get("compiler_version") or "",
            OptimizationUsed="1" if contracts_verification.get("optimization_used") else "0",
            Runs=str(contracts_verification.get("optimization_runs") or ""),
            ConstructorArguments=contracts_verification.get("constructor_arguments") or "",
            EVMVersion=contracts_verification.get("evm_version") or "",
            Library=(
                ",".join(contracts_verification.get("libraries", [])) if contracts_verification.get("libraries") else ""
            ),
            LicenseType=contracts_verification.get("license_type") or "",
            Proxy="1" if contracts_verification.get("proxy") else "0",
            Implementation=contracts_verification.get("implementation") or "",
        )
    ]

    return output_data


# Get Historical ERC20-Token TotalSupply by ContractAddress & BlockNo (TODO)
# Get Address ERC721 Token Inventory By Contract Address (TODO)
# Get Daily Average Network Hash Rate (TODO)
# Get Daily Average Network Difficulty (TODO)
# Get Ether Historical Daily Market Cap (TODO)
# Get Ether Historical Price (TODO)
