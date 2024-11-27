from api.app.cache import cache
from api.app.contract.contract_verify import get_contract_names
from api.app.ens.ens import ENSClient
from common.models import db
from common.models.contracts import Contracts
from common.models.tokens import Tokens
from common.utils.config import get_config
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from custom_jobs.address_index.models.address_index_stats import AddressIndexStats

app_config = get_config()

if app_config.ens_service is not None and app_config.ens_service != "":
    ens_client = ENSClient(app_config.ens_service)
else:
    ens_client = None

token_address_transfers_type_column_dict = {
    "tokentxns": AddressIndexStats.erc20_transfer_count,
    "tokentxns-nft": AddressIndexStats.nft_721_transfer_count,
    "tokentxns-nft1155": AddressIndexStats.nft_1155_transfer_count,
    "erc20": AddressIndexStats.erc20_transfer_count,
    "erc721": AddressIndexStats.nft_721_transfer_count,
    "erc1155": AddressIndexStats.nft_1155_transfer_count,
}


def type_to_stats_column(type):
    return token_address_transfers_type_column_dict[type]


def get_token_txn_cnt_by_address(token_type, bytes_address: bytes):
    result = (
        db.session.query(AddressIndexStats)
        .with_entities(type_to_stats_column(token_type))
        .filter(AddressIndexStats.address == bytes_address)
        .first()
    )

    return result


def get_txn_cnt_by_address(address: str):
    bytes_address = hex_str_to_bytes(address)
    result = (
        db.session.query(AddressIndexStats)
        .with_entities(AddressIndexStats.transaction_count)
        .filter(AddressIndexStats.address == bytes_address)
        .first()
    )
    return result


@cache.memoize(3600)
def get_address_display_mapping(bytea_address_list: list[bytes]):
    if not bytea_address_list or len(bytea_address_list) == 0:
        return {}

    # filter not valid address
    bytea_address_list = [address for address in bytea_address_list if address]
    str_address_list = [bytes_to_hex_str(address) for address in bytea_address_list]

    # str -> str
    address_map = {}

    # Contract + Proxy Contract
    proxy_mapping_result = (
        db.session.query(Contracts.address, Contracts.verified_implementation_contract)
        .filter(
            Contracts.address.in_(bytea_address_list),
            Contracts.verified_implementation_contract != None,
        )
        .all()
    )
    # bytea -> bytea
    proxy_mapping = {}
    for address in proxy_mapping_result:
        proxy_mapping[address.address] = address.verified_implementation_contract

    # Get name for all the potential contracts, including proxy implementations
    str_contract_list = str_address_list + [bytes_to_hex_str(address) for address in proxy_mapping.values()]
    contract_addresses = get_contract_names(str_contract_list)

    # update address to contract name mapping
    address_map.update({address.get("address"): address.get("contract_name") for address in contract_addresses})

    # If an implementation address has name, overwrite the proxy contract
    for proxy_address, implementation_address in proxy_mapping.items():
        str_proxy_address = bytes_to_hex_str(proxy_address)
        str_implementation_address = bytes_to_hex_str(implementation_address)
        if str_implementation_address in address_map:
            address_map[str_proxy_address] = address_map[str_implementation_address]

    # Token
    addresses = (
        db.session.query(Tokens.address, Tokens.name, Tokens.symbol)
        .filter(
            Tokens.address.in_(bytea_address_list),
        )
        .all()
    )
    for address in addresses:
        str_address = bytes_to_hex_str(address.address)
        address_map[str_address] = "{}: {} Token".format(address.name, address.symbol)

    # ENS
    if ens_client:
        addresses = ens_client.batch_get_address_ens(str_address_list)
        for key, value in addresses.items():
            address_map[key] = value

    # Any additional manual tags
    addresses = (
        db.session.query(AddressIndexStats.address, AddressIndexStats.tag)
        .filter(
            AddressIndexStats.address.in_(bytea_address_list),
            AddressIndexStats.tag != None,
        )
        .all()
    )

    for address in addresses:
        str_address = bytes_to_hex_str(address.address)
        address_map[str_address] = address.tag

    return address_map


@cache.memoize(3600)
def get_ens_mapping(wallet_address_list):
    if ens_client:
        address_map = ens_client.batch_get_address_ens(wallet_address_list)

    return address_map
