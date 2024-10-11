from datetime import datetime
from typing import List, Union

from sqlalchemy import and_, func

from api.app.address.models import ScheduledMetadata
from common.models import db
from common.utils.format_utils import as_dict, format_to_dict, hex_str_to_bytes
from indexer.modules.custom.address_index.models.address_contract_operation import AddressContractOperations
from indexer.modules.custom.address_index.models.address_index_daily_stats import AddressIndexDailyStats

PAGE_SIZE = 10


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
    return get_address_hist_stats(
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
    return get_address_hist_stats(
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
    return get_address_hist_stats(
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
    return get_address_hist_stats(
        address,
        [
            "contract_creation_count",
            "contract_destruction_count",
            "contract_operation_count",
        ],
        start_time,
        end_time,
    )


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
            query = query.add_columns(func.sum(getattr(AddressIndexDailyStats, a)).label(a))
        else:
            raise ValueError(f"Invalid attribute: {a}")

    filters = [AddressIndexDailyStats.address == address]
    if start_time:
        filters.append(AddressIndexDailyStats.block_date >= start_time.date())
    if end_time:
        filters.append(AddressIndexDailyStats.block_date <= end_time.date())

    query = query.filter(and_(*filters))

    query = query.group_by(AddressIndexDailyStats.block_date)

    result = query.one_or_none()

    return as_dict(result)
