import binascii
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, func

from api.app.address.features import register_feature
from api.app.address.models import AddressBaseProfile, ScheduledMetadata
from api.app.utils.token_utils import get_coin_prices, get_latest_coin_prices
from api.app.web3_utils import get_balance
from common.models import db
from common.models.contracts import Contracts
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_coin_value, format_to_dict, format_value_for_json
from indexer.modules.custom.address_index.address_index_job import AddressTransactionType, InternalTransactionType
from indexer.modules.custom.address_index.models.address_contract_operation import AddressContractOperations
from indexer.modules.custom.address_index.models.address_index_daily_stats import AddressIndexDailyStats
from indexer.modules.custom.address_index.models.address_internal_transaciton import AddressInternalTransactions
from indexer.modules.custom.address_index.models.address_token_holders import AddressTokenHolders
from indexer.modules.custom.address_index.models.address_transactions import AddressTransactions
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

    return {
        "total_volume_eth": str(total_volume_eth),
        "total_volume_usd": str(total_volume_usd),
        "total_gas_fee_used_eth": str(total_gas_fee_used_eth),
        "total_gas_fee_used_usd": str(total_gas_fee_used_usd),
        "average_daily_volume_eth": str(total_volume_eth / len(daily_volumes)) if daily_volumes else "0",
        "average_daily_volume_usd": str(total_volume_usd / len(daily_volumes)) if daily_volumes else "0",
    }


def get_wallet_address_token_holdings(wallet_address: Optional[Union[str, bytes]]):
    if isinstance(wallet_address, str):
        address_bytes = binascii.unhexlify(wallet_address[2:])
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
                        "balance": float(int(holder.balance_of) / (10**token.decimals or 0)),
                        "token": {
                            "address": "0x" + holder.token_address.hex(),
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
                        "tvl": float(int(holder.balance_of) / (10**token.decimals or 0)) * float(token.price or 0),
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
    address_bytes = bytes.fromhex(address[2:]) if isinstance(address, str) else address

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
        address = bytes.fromhex(address[2:])
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
        address = bytes.fromhex(address[2:])
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
        address = bytes.fromhex(address[2:])
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
        address = bytes.fromhex(address[2:])

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
        address = bytes.fromhex(address[2:])

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
    token_holding = get_wallet_address_token_holdings(address)
    tvl = float(get_balance(address) / 10**18) * get_latest_coin_prices() + sum([x["tvl"] for x in token_holding])

    return {
        "total_asset_value_usd": tvl,
        "coin_balance": coin_balance,
        "holdings": token_holding,
    }
