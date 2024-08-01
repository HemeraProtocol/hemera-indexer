import binascii

from api.app.cache import cache
from api.app.contract.contract_verify import get_contract_names
from api.app.ens.ens import ENSClient
from common.models import db
from common.models.contracts import Contracts
from common.models.statistics_wallet_addresses import StatisticsWalletAddresses
from common.models.tokens import Tokens
from common.utils.config import get_config
from common.utils.db_utils import build_entities

app_config = get_config()

if app_config.ens_service is not None and app_config.ens_service != "":
    ens_client = ENSClient(app_config.ens_service)
else:
    ens_client = None

token_address_transfers_type_column_dict = {
    "tokentxns": StatisticsWalletAddresses.erc20_transfer_cnt,
    "tokentxns-nft": StatisticsWalletAddresses.erc721_transfer_cnt,
    "tokentxns-nft1155": StatisticsWalletAddresses.erc1155_transfer_cnt, 
    "erc20": StatisticsWalletAddresses.erc20_transfer_cnt,
    "erc721": StatisticsWalletAddresses.erc721_transfer_cnt,
    "erc1155": StatisticsWalletAddresses.erc1155_transfer_cnt,
}


def type_to_stats_column(type):
    return token_address_transfers_type_column_dict[type]


def get_token_txn_cnt_by_address(token_type, address):
    bytes_address = bytes.fromhex(address[2:])
    result = (
        db.session.query(StatisticsWalletAddresses)
        .with_entities(type_to_stats_column(token_type))
        .filter(StatisticsWalletAddresses.address == bytes_address)
        .first()
    )

    return result


def get_txn_cnt_by_address(address):
    bytes_address = bytes.fromhex(address[2:])
    result = (
        db.session.query(StatisticsWalletAddresses)
        .with_entities(StatisticsWalletAddresses.txn_cnt)
        .filter(StatisticsWalletAddresses.address == bytes_address)
        .first()
    )
    return result


@cache.memoize(3600)
def get_address_display_mapping(bytea_address_list: list[bytes]):
    if not bytea_address_list or len(bytea_address_list) == 0:
        return {}

    # filter not valid address
    bytea_address_list = [address for address in bytea_address_list if address]
    str_address_list = ['0x' + address.hex() for address in bytea_address_list]

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
    str_contract_list = str_address_list + ['0x' + address.hex() for address in proxy_mapping.values()]
    contract_addresses = get_contract_names(str_contract_list)

    # update address to contract name mapping
    address_map.update({address.get("address"): address.get("contract_name") for address in contract_addresses})

    # If an implementation address has name, overwrite the proxy contract
    for proxy_address, implementation_address in proxy_mapping.items():
        str_proxy_address = '0x' + proxy_address.hex()
        str_implementation_address =  '0x' + implementation_address.hex()
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
        str_address = "0x" + address.address.hex()
        address_map[str_address] = "{}: {} Token".format(address.name, address.symbol)

    # ENS
    if ens_client:
        addresses = ens_client.batch_get_address_ens(str_address_list)
        for key, value in addresses.items():
            address_map[key] = value

    # Any additional manual tags
    addresses = (
        db.session.query(StatisticsWalletAddresses.address, StatisticsWalletAddresses.tag)
        .filter(
            StatisticsWalletAddresses.address.in_(bytea_address_list),
            StatisticsWalletAddresses.tag != None,
        )
        .all()
    )

    for address in addresses:
        str_address = "0x" + address.address.hex()
        address_map[str_address] = address.tag

    return address_map


@cache.memoize(3600)
def get_ens_mapping(wallet_address_list):
    if ens_client:
        address_map = ens_client.batch_get_address_ens(wallet_address_list)

    return address_map
