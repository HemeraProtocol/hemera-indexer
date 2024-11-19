import binascii
from datetime import date, datetime
from select import select
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, func

from api.app.address.features import register_feature
from api.app.address.models import AddressBaseProfile, ScheduledMetadata
from api.app.utils.format_utils import format_coin_value
from api.app.utils.token_utils import get_coin_prices, get_latest_coin_prices
from api.app.utils.web3_utils import get_balance
from common.models import db
from common.models.contracts import Contracts
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, bytes_to_hex_str, format_to_dict, format_value_for_json, hex_str_to_bytes
from enumeration.token_type import TokenType
from indexer.modules.custom.address_index.address_index_job import AddressTransactionType, InternalTransactionType
from indexer.modules.custom.address_index.models.address_contract_operation import AddressContractOperations
from indexer.modules.custom.address_index.models.address_index_daily_stats import AddressIndexDailyStats
from indexer.modules.custom.address_index.models.address_internal_transaciton import AddressInternalTransactions
from indexer.modules.custom.address_index.models.address_nft_1155_holders import AddressNftTokenHolders
from indexer.modules.custom.address_index.models.address_token_holders import AddressTokenHolders
from indexer.modules.custom.address_index.models.address_transactions import AddressTransactions
from indexer.modules.custom.address_index.models.token_address_nft_inventories import TokenAddressNftInventories
from indexer.modules.custom.address_index.schemas.api import address_base_info_model, filter_and_fill_dict_by_model

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000


@register_feature("contract_deployer", "value")
def get_contract_deployer_profile(address) -> Optional[Dict[str, Any]]:
    address_deploy_contract_count = get_address_deploy_contract_count(address)
    address_first_deploy_contract_time = get_address_first_deploy_contract_time(address)
    return (
        {
            "deployed_contract_count": address_deploy_contract_count,
            "first_deployed_time": address_first_deploy_contract_time,
        }
        if address_deploy_contract_count != 0
        else None
    )


@register_feature("contract_deployer", "events")
def get_contract_deployed_events(address, limit=5, offset=0) -> Optional[Dict[str, Any]]:
    count = get_address_deploy_contract_count(address)
    if count == 0:
        return None
    events = get_address_contract_operations(address, limit=limit, offset=offset)
    res = []
    for event in events:
        res.append(format_to_dict(event))
    return {"data": res, "total": count}


def get_wallet_address_volumes(wallet_address: Optional[Union[str, bytes]], coin_symbol: str = "ETH"):
    transaction_values = get_address_hist_stats(
        wallet_address,
        ["transaction_in_value", "transaction_out_value", "transaction_out_fee"],
    )

    block_date_list = [x["block_date"] for x in transaction_values]
    prices = get_coin_prices(block_date_list)
    prices_dict = {x["block_date"]: x["price"] for x in prices}

    daily_volumes = []
    total_volume_eth = 0
    total_volume_usd = 0

    total_gas_fee_used_eth = 0
    total_gas_fee_used_usd = 0

    for value in transaction_values:
        date = value["block_date"]
        volume_eth = (value["transaction_in_value"] + value["transaction_out_value"]) / 10**18
        gas_fee_used = value["transaction_out_fee"] / 10**18
        price = prices_dict.get(date, 0)
        volume_usd = volume_eth * price
        total_gas_fee_used_usd += gas_fee_used * price
        daily_volumes.append(
            {
                "date": date,
                "volume_eth": str(volume_eth),
                "price": str(price),
                "volume_usd": str(volume_usd),
                "gas_fee_used": str(gas_fee_used),
            }
        )

        total_volume_eth += volume_eth
        total_volume_usd += volume_usd
        total_gas_fee_used_eth += gas_fee_used
        total_gas_fee_used_usd += total_gas_fee_used_usd

        daily_volumes.sort(key=lambda x: x["date"])
        interval_day: int = (
            (daily_volumes[-1].get("date") - daily_volumes[0].get("date")).days if len(daily_volumes) > 1 else 1
        )

    return {
        "total_volume_eth": str(total_volume_eth),
        "total_volume_usd": str(total_volume_usd),
        "total_gas_fee_used_eth": str(total_gas_fee_used_eth),
        "total_gas_fee_used_usd": str(total_gas_fee_used_usd),
        "average_daily_volume_eth": str(total_volume_eth / interval_day) if daily_volumes else "0",
        "average_daily_volume_usd": str(total_volume_usd / interval_day) if daily_volumes else "0",
    }


def get_wallet_address_nft_holdings(wallet_address: Optional[Union[str, bytes]]):
    if isinstance(wallet_address, str):
        address_bytes = hex_str_to_bytes(wallet_address)
    else:
        address_bytes = wallet_address

    query_721 = db.session.query(
        TokenAddressNftInventories.token_address,
        func.array_agg(TokenAddressNftInventories.token_id).label("token_ids"),
        func.count(TokenAddressNftInventories.token_id).label("nft_count"),
    )
    query_721 = query_721.filter(TokenAddressNftInventories.wallet_address == address_bytes)
    query_721 = query_721.group_by(TokenAddressNftInventories.token_address)

    query_1155 = db.session.query(
        AddressNftTokenHolders.token_address,
        func.array_agg(AddressNftTokenHolders.token_id).label("token_ids"),
        func.array_agg(AddressNftTokenHolders.balance_of).label("token_amounts"),
        func.count(AddressNftTokenHolders.balance_of).label("nft_count"),
    )
    query_1155 = query_1155.filter(AddressNftTokenHolders.address == address_bytes).filter(
        AddressNftTokenHolders.balance_of > 0
    )
    query_1155 = query_1155.group_by(AddressNftTokenHolders.token_address)

    holdings_721 = query_721.all()
    holdings_1155 = query_1155.all()

    nft_holders = []
    for row in holdings_721:
        token_address, token_ids, nft_count = row
        nft_holders.append(
            {
                "token_address": token_address,
                "token_ids": [str(token_id) for token_id in token_ids],
                "amounts": ["1" for _ in range(len(token_ids))],
                "balance": str(nft_count),
                "token_type": TokenType.ERC721.value,
            }
        )

    for row in holdings_1155:
        token_address, token_ids, token_amounts, nft_count = row
        total_balance = sum(int(amount) for amount in token_amounts)
        nft_holders.append(
            {
                "token_address": token_address,
                "token_ids": [str(token_id) for token_id in token_ids],
                "amounts": [str(amount) for amount in token_amounts],
                "balance": str(total_balance),
                "token_type": TokenType.ERC1155.value,
            }
        )

    token_addresses = [holder["token_address"] for holder in nft_holders]
    tokens = Tokens.query.filter(
        and_(
            Tokens.address.in_(token_addresses),
            Tokens.token_type.in_([TokenType.ERC1155.value, TokenType.ERC721.value]),
            Tokens.is_verified == True,
        )
    ).all()

    token_map = {}
    for token in tokens:
        token_map[token.address] = token

    res = []
    for holder in nft_holders:
        if holder["token_address"] in token_map:
            token = token_map[holder["token_address"]]
            estimated_value = float(token.price or 0) * float(holder["balance"])

            res.append(
                format_value_for_json(
                    {
                        "token": {
                            "address": holder["token_address"],
                            "token_name": token.name,
                            "token_symbol": token.symbol,
                            "token_logo_url": token.icon_url,
                            "token_type": holder["token_type"],
                            "extra_info": {"floor_price": token.price},
                        },
                        "balance": sum([int(amount) for amount in holder["amounts"]]),
                        "token_ids": holder["token_ids"],
                        "amounts": holder["amounts"],
                        "estimated_value_usd": estimated_value,
                    }
                )
            )

    return res


def get_wallet_address_token_holdings(wallet_address: Optional[Union[str, bytes]]):
    if isinstance(wallet_address, str):
        address_bytes = hex_str_to_bytes(wallet_address)
    else:
        address_bytes = wallet_address

    query = db.session.query(AddressTokenHolders)
    query = query.filter(AddressTokenHolders.address == address_bytes)
    query = query.filter(AddressTokenHolders.balance_of > 0)

    holdings = query.all()

    token_addresses = [(holding.token_address) for holding in holdings]

    tokens = Tokens.query.filter(
        and_(
            Tokens.address.in_(token_addresses),
            Tokens.token_type == TokenType.ERC20.value,
            Tokens.is_verified == True,
        )
    ).all()

    token_map = {}
    res = []
    for token in tokens:
        token_map[token.address] = token
    for holder in holdings:
        if holder.token_address in token_map:
            token = token_map[holder.token_address]
            res.append(
                format_value_for_json(
                    {
                        "balance": float(int(holder.balance_of) / (10 ** (token.decimals or 0))),
                        "token": {
                            "address": bytes_to_hex_str(holder.token_address),
                            "token_name": token.name,
                            "token_symbol": token.symbol,
                            "token_logo_url": token.icon_url,
                            "token_type": token.token_type,
                            "extra_info": {
                                "volume_24h": token.volume_24h,
                                "price": token.price or 0,
                                "previous_price": token.previous_price,
                                "market_cap": token.market_cap,
                                "on_chain_market_cap": token.on_chain_market_cap,
                                "cmc_id": token.cmc_id,
                                "cmc_slug": token.cmc_slug,
                                "gecko_id": token.gecko_id,
                            },
                        },
                        "estimated_value_usd": float(int(holder.balance_of) / (10**token.decimals or 0))
                        * float(token.price or 0),
                    }
                )
            )
    return res


def get_address_recent_info(address: bytes, latest_timestamp) -> Optional[dict]:
    """
    Fetch recent transaction data from AddressOpenseaTransactions.
    """
    contract = db.session.query(Contracts).filter_by(address=address).first()
    if contract:
        return {
            "creation_code": contract.creation_code,
            "deployed_code": contract.deployed_code,
            "deployed_block_timestamp": contract.block_timestamp,
            "deployed_block_number": contract.block_number,
            "deployed_block_hash": contract.block_hash,
            "deployed_transaction_hash": contract.transaction_hash,
            "deployed_internal_transaction_from_address": contract.transaction_from_address,
            "is_contract": True,
        }

    internal_transaction_query = db.session.query(AddressInternalTransactions).filter(
        AddressInternalTransactions.address == address,
        AddressInternalTransactions.call_type == "call",
        AddressInternalTransactions.txn_type == InternalTransactionType.RECEIVER.value,
    )

    if latest_timestamp is not None:
        internal_transaction_query = internal_transaction_query.filter(
            AddressInternalTransactions.block_timestamp > latest_timestamp
        )

    internal_transaction = internal_transaction_query.order_by(
        AddressInternalTransactions.block_timestamp.asc()
    ).first()

    init_funding = {}
    if internal_transaction:
        init_funding = {
            "init_funding_from_address": internal_transaction.related_address,
            "init_funding_value": int(internal_transaction.value),
            "init_funding_transaction_hash": internal_transaction.transaction_hash,
            "init_funding_block_timestamp": internal_transaction.block_timestamp,
            "init_block_hash": internal_transaction.block_hash,
            "init_block_number": internal_transaction.block_number,
        }

    transaction_query = db.session.query(AddressTransactions).filter(
        AddressTransactions.address == address,
        AddressTransactions.txn_type == AddressTransactionType.SENDER.value,
    )

    if latest_timestamp is not None:
        transaction_query = transaction_query.filter(AddressTransactions.block_timestamp > latest_timestamp)

    transaction = transaction_query.order_by(AddressTransactions.block_timestamp.asc()).first()

    sent_transaction = {}
    if transaction:
        sent_transaction = {
            "first_transaction_hash": transaction.transaction_hash,
            "first_block_hash": transaction.block_hash,
            "first_block_number": transaction.block_number,
            "first_block_timestamp": transaction.block_timestamp,
            "first_to_address": transaction.related_address,
        }

    return format_value_for_json(init_funding | sent_transaction) if init_funding or sent_transaction else None


def get_latest_transaction_by_address(address: bytes) -> Optional[dict]:
    """
    Fetch the latest transaction by address.
    """
    transaction = (
        db.session.query(AddressTransactions)
        .filter(
            AddressTransactions.address == address,
            AddressTransactions.txn_type == AddressTransactionType.SENDER.value,
        )
        .order_by(AddressTransactions.block_timestamp.desc())
        .first()
    )

    if transaction:
        return format_value_for_json(
            {
                "latest_transaction_hash": transaction.transaction_hash,
                "latest_block_hash": transaction.block_hash,
                "latest_block_number": transaction.block_number,
                "latest_block_timestamp": transaction.block_timestamp,
                "latest_to_address": transaction.related_address,
            }
        )
    return {}


def get_address_agg_stats(
    address: Union[str, bytes], start_date: Optional[date] = None, end_date: Optional[date] = None
) -> dict:
    aggregated_stats = get_address_hist_agg_stats(
        address,
        [
            "transaction_in_count",
            "transaction_out_count",
            "transaction_self_count",
            "transaction_in_value",
            "transaction_out_value",
            "transaction_self_value",
            "transaction_in_fee",
            "transaction_out_fee",
            "transaction_self_fee",
            "internal_transaction_in_count",
            "internal_transaction_out_count",
            "internal_transaction_self_count",
            "internal_transaction_in_value",
            "internal_transaction_out_value",
            "internal_transaction_self_value",
            "transaction_count",
            "internal_transaction_count",
        ],
        start_date,
        end_date,
    )
    values_fields = [
        "internal_transaction_self_value",
        "internal_transaction_out_value",
        "internal_transaction_in_value",
        "transaction_in_value",
        "transaction_out_value",
        "transaction_self_value",
        "transaction_in_fee",
        "transaction_out_fee",
        "transaction_self_fee",
    ]
    for field in values_fields:
        if field in aggregated_stats:
            aggregated_stats[field] = format_coin_value(aggregated_stats[field])
    return aggregated_stats


def get_address_base_info(address: Union[str, bytes]) -> dict:
    """
    Fetch and combine address profile data from both the base profile and recent transactions.
    """
    address_bytes = hex_str_to_bytes(address) if isinstance(address, str) else address

    # Fetch the base profile
    base_profile = db.session.query(AddressBaseProfile).filter_by(address=address_bytes).first()
    if not base_profile:
        raise APIError("No profile found for this address", code=400)

    # Convert base profile to a dictionary
    base_profile_data = as_dict(base_profile)

    # Fetch the latest scheduled metadata timestamp
    latest_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()

    # Fetch recent transaction data from AddressOpenseaTransactions
    recent_data = get_address_recent_info(address_bytes, latest_timestamp) if base_profile_data is None else {}

    # Merge recent transaction data with base profile data
    base_profile_data |= recent_data

    # Fetch the latest transaction
    latest_transaction = get_latest_transaction_by_address(address_bytes)

    agg_stats = get_address_agg_stats(address_bytes)

    # Combine and return the base profile, recent data, and latest transaction
    res = base_profile_data | latest_transaction | agg_stats

    if res.get("init_funding_value"):
        res["init_funding_value"] = format_coin_value(res["init_funding_value"])

    res = filter_and_fill_dict_by_model(res, address_base_info_model)
    return res


def get_address_first_deploy_contract_time(address: Union[str, bytes]) -> datetime:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    first_deploy_contract = (
        db.session.query(AddressContractOperations.block_timestamp)
        .filter(
            AddressContractOperations.address == address,
            AddressContractOperations.trace_type.in_(["create", "create2"]),
        )
        .order_by(AddressContractOperations.block_timestamp)
        .first()
    )
    return format_to_dict(first_deploy_contract[0]) if first_deploy_contract else None


def convert_to_developer_info(
    first_record: AddressContractOperations, latest_record: AddressContractOperations, deployed_count: int
) -> Dict[str, Any]:
    """
    Convert AddressContractOperations records to developer info model format

    Args:
        first_record: First deployment record
        latest_record: Latest deployment record
        deployed_count: Total number of deployed contracts
    """

    if not first_record:
        return None

    result = {
        "address": bytes_to_hex_str(first_record.address),
        "deployed_contracts_count": deployed_count,
        # First contract info
        "first_contract_deployed_address": bytes_to_hex_str(first_record.contract_address),
        "first_contract_deployed_transaction_hash": bytes_to_hex_str(first_record.transaction_hash),
        "first_contract_deployed_block_hash": bytes_to_hex_str(first_record.block_hash),
        "first_contract_deployed_block_number": first_record.block_number,
        "first_contract_deployed_block_timestamp": first_record.block_timestamp,
        "first_contract_deployed_trace_id": first_record.trace_id,
    }

    if latest_record and latest_record != first_record:
        result.update(
            {
                "latest_contract_deployed_address": bytes_to_hex_str(latest_record.contract_address),
                "latest_contract_deployed_transaction_hash": bytes_to_hex_str(latest_record.transaction_hash),
                "latest_contract_deployed_block_hash": bytes_to_hex_str(latest_record.block_hash),
                "latest_contract_deployed_block_number": latest_record.block_number,
                "latest_contract_deployed_block_timestamp": latest_record.block_timestamp,
                "latest_contract_deployed_trace_id": latest_record.trace_id,
            }
        )
    else:
        result.update(
            {
                "latest_contract_deployed_address": result["first_contract_deployed_address"],
                "latest_contract_deployed_transaction_hash": result["first_contract_deployed_transaction_hash"],
                "latest_contract_deployed_block_hash": result["first_contract_deployed_block_hash"],
                "latest_contract_deployed_block_number": result["first_contract_deployed_block_number"],
                "latest_contract_deployed_block_timestamp": result["first_contract_deployed_block_timestamp"],
                "latest_contract_deployed_trace_id": result["first_contract_deployed_trace_id"],
            }
        )

    return result


def get_address_contract_development_stats(address: Union[str, bytes]) -> Dict[str, Any]:
    """
    Get contract development statistics for a given address.
    Calculates total transaction output count and fees for all contracts deployed by this address.

    Args:
        address: Target address in string or bytes format

    Returns:
        Dict containing contract stats including transaction counts and gas fees in ETH/USD
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    contracts_subquery = (
        db.session.query(Contracts.address).filter(Contracts.transaction_from_address == address).subquery()
    )

    daily_stats = (
        db.session.query(
            AddressIndexDailyStats.block_date,
            func.sum(AddressIndexDailyStats.transaction_out_count).label("tx_count"),
            func.sum(AddressIndexDailyStats.transaction_out_fee).label("tx_fee"),
        )
        .filter(AddressIndexDailyStats.address.in_(db.session.query(contracts_subquery.c.address)))
        .group_by(AddressIndexDailyStats.block_date)
        .all()
    )

    block_dates = [stat.block_date for stat in daily_stats]
    prices = get_coin_prices(block_dates)
    prices_dict = {x["block_date"]: x["price"] for x in prices}

    total_tx_count = 0
    total_gas_eth = 0
    total_gas_usd = 0

    for stat in daily_stats:
        gas_fee_eth = stat.tx_fee / 10**18
        price = prices_dict.get(stat.block_date, 0)
        gas_fee_usd = float(gas_fee_eth) * float(price)

        total_tx_count += stat.tx_count
        total_gas_eth += gas_fee_eth
        total_gas_usd += gas_fee_usd

    return {
        "total_transaction_count_across_contract": total_tx_count,
        "total_gas_consumed_across_contracts_eth": total_gas_eth,
        "total_gas_consumed_across_contracts_usd": total_gas_usd,
    }


def get_address_developer_info(address: Union[str, bytes]) -> Dict[str, Any]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    base_query = db.session.query(AddressContractOperations).filter(
        AddressContractOperations.address == address,
        AddressContractOperations.trace_type.in_(["create", "create2"]),
        AddressContractOperations.transaction_receipt_status == 1,
    )

    deployed_count = base_query.count()

    if deployed_count == 0:
        return {}

    first_record = base_query.order_by(AddressContractOperations.block_timestamp).first()
    latest_record = (
        base_query.order_by(AddressContractOperations.block_timestamp.desc()).first()
        if deployed_count > 1
        else first_record
    )
    developer_info = convert_to_developer_info(first_record, latest_record, deployed_count)
    address_contract_development_stats = get_address_contract_development_stats(address)
    return developer_info | address_contract_development_stats


def get_address_deploy_contract_count(address: Union[str, bytes]) -> int:
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()
    if not last_timestamp:
        return get_address_deploy_contract_count_before_date(address)
    else:
        return get_address_hist_deploy_contract_count(
            address, end_time=last_timestamp
        ) + get_address_deploy_contract_count_before_date(address, start_time=last_timestamp)


def get_address_hist_deploy_contract_count(
    address: Union[str, bytes], start_time: datetime = None, end_time: datetime = None
) -> int:
    return get_address_hist_contract_stats(address, start_time, end_time).get("contract_creation_count", 0)


def get_address_deploy_contract_count_before_date(address: Union[str, bytes], start_time: datetime = None) -> int:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if start_time:
        count = (
            db.session.query(AddressContractOperations)
            .filter(
                AddressContractOperations.address == address,
                AddressContractOperations.block_timestamp >= start_time,
                AddressContractOperations.trace_type in ["create", "create2"],
            )
            .count()
        )
    else:
        count = db.session.query(AddressContractOperations).filter(AddressContractOperations.address == address).count()
    return count


def get_address_contract_operations(address: Union[str, bytes], limit=5, offset=0) -> list[dict]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    transactions = (
        db.session.query(AddressContractOperations)
        .order_by(
            AddressContractOperations.block_number.desc(),
            AddressContractOperations.transaction_index.desc(),
            AddressContractOperations.trace_id.desc(),
        )
        .filter(AddressContractOperations.address == address)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions


def get_address_hist_transaction_stats(
    address: Union[str, bytes], start_time: datetime = None, end_time: datetime = None
):
    return get_address_hist_agg_stats(
        address,
        [
            "transaction_count",
            "transaction_in_count",
            "transaction_out_count",
            "transaction_self_count",
            "transaction_in_value",
            "transaction_out_value",
            "transaction_self_value",
            "transaction_in_fee",
            "transaction_out_fee",
            "transaction_self_fee",
        ],
        start_time,
        end_time,
    )


def get_address_hist_internal_transaction_stats(
    address: Union[str, bytes], start_time: datetime = None, end_time: datetime = None
):
    return get_address_hist_agg_stats(
        address,
        [
            "internal_transaction_count",
            "internal_transaction_in_count",
            "internal_transaction_out_count",
            "internal_transaction_self_count",
            "internal_transaction_in_value",
            "internal_transaction_out_value",
            "internal_transaction_self_value",
        ],
        start_time,
        end_time,
    )


def get_address_hist_token_transfer_stats(
    address: Union[str, bytes], start_time: datetime = None, end_time: datetime = None
):
    return get_address_hist_agg_stats(
        address,
        [
            "erc20_transfer_count",
            "erc20_transfer_in_count",
            "erc20_transfer_out_count",
            "erc20_transfer_self_count",
            "nft_transfer_count",
            "nft_transfer_in_count",
            "nft_transfer_out_count",
            "nft_transfer_self_count",
        ],
        start_time,
        end_time,
    )


def get_address_hist_contract_stats(address: Union[str, bytes], start_time: datetime = None, end_time: datetime = None):
    return get_address_hist_agg_stats(
        address,
        [
            "contract_creation_count",
            "contract_destruction_count",
            "contract_operation_count",
        ],
        start_time,
        end_time,
    )


def get_address_hist_agg_stats(
    address: Union[str, bytes], attr: Union[str, List[str]], start_time: datetime = None, end_time: datetime = None
):
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    if isinstance(attr, str):
        attr = [attr]

    query = db.session.query()

    for a in attr:
        if hasattr(AddressIndexDailyStats, a):
            query = query.add_columns(func.sum(getattr(AddressIndexDailyStats, a)).label(a))
        else:
            raise ValueError(f"Invalid attribute: {a}")

    filters = [AddressIndexDailyStats.address == address]
    if start_time:
        filters.append(AddressIndexDailyStats.block_date >= start_time.date())
    if end_time:
        filters.append(AddressIndexDailyStats.block_date <= end_time.date())

    query = query.filter(and_(*filters))

    result = query.one_or_none()

    return format_to_dict(result) if result else None


def get_address_hist_stats(
    address: Union[str, bytes], attr: Union[str, List[str]], start_time: datetime = None, end_time: datetime = None
):
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    if isinstance(attr, str):
        attr = [attr]

    query = db.session.query(AddressIndexDailyStats.block_date)

    for a in attr:
        if hasattr(AddressIndexDailyStats, a):
            query = query.add_columns(getattr(AddressIndexDailyStats, a))
        else:
            raise ValueError(f"Invalid attribute: {a}")

    filters = [AddressIndexDailyStats.address == address]
    if start_time:
        filters.append(AddressIndexDailyStats.block_date >= start_time.date())
    if end_time:
        filters.append(AddressIndexDailyStats.block_date <= end_time.date())

    query = query.filter(and_(*filters))
    query = query.order_by(AddressIndexDailyStats.block_date)

    results = query.all()

    return [format_to_dict(result) for result in results] if results else []


def get_address_assets(address: Union[str, bytes]) -> dict:
    coin_balance = format_coin_value(get_balance(address))
    token_holdings = get_wallet_address_token_holdings(address)
    nft_holdings = get_wallet_address_nft_holdings(address)
    token_estimated_value_usd = sum([x["estimated_value_usd"] for x in token_holdings])
    nft_estimated_value_usd = sum([x["estimated_value_usd"] for x in nft_holdings])
    tvl = (
        float(get_balance(address) / 10**18) * get_latest_coin_prices()
        + token_estimated_value_usd
        + nft_estimated_value_usd
    )

    return {
        "total_asset_value_usd": tvl,
        "coin_balance": coin_balance,
        "holdings": token_holdings,
        "token_holdings": token_holdings,
        "nft_holdings": nft_holdings,
        "token_estimated_value_usd": token_estimated_value_usd,
        "nft_estimated_value_usd": nft_estimated_value_usd,
    }
