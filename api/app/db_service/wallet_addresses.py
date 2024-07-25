import binascii

from common.models import db
from common.models.contracts import Contracts
from common.models.tokens import Tokens
from common.models.statistics_wallet_addresses import StatisticsWalletAddresses
from common.utils.config import get_config
from common.utils.db_utils import build_entities
from api.app.cache import cache
from api.app.contract.contract_verify import get_contract_names
from api.app.ens.ens import ENSClient

app_config = get_config()

if app_config.ens_service is not None and app_config.ens_service != "":
    ens_client = ENSClient(app_config.ens_service)
else:
    ens_client = None

token_address_transfers_type_column_dict = {
    "tokentxns": StatisticsWalletAddresses.erc20_transfer_cnt,
    "tokentxns-nft": StatisticsWalletAddresses.erc721_transfer_cnt,
    "tokentxns-nft1155": StatisticsWalletAddresses.erc1155_transfer_cnt,
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
def get_address_display_mapping(wallet_address_list: list[bytes]):
    # filter not valid address
    wallet_address_list = [address for address in wallet_address_list if address]
    str_address_list = ['0x' + address.hex() for address in wallet_address_list]
    if not wallet_address_list or len(wallet_address_list) == 0:
        return {}

    address_map = {}

    # 合约 + 代理合约
    proxy_mapping_result = (
        db.session.query(Contracts.address, Contracts.verified_implementation_contract)
        .filter(
            Contracts.address.in_(wallet_address_list),
            Contracts.verified_implementation_contract != None,
        )
        .all()
    )
    proxy_mapping = {}
    for address in proxy_mapping_result:
        proxy_mapping[address.address] = address.verified_implementation_contract

    # 获取所有地址的合约名称
    all_addresses = list(wallet_address_list) + list(proxy_mapping.values())
    addresses = get_contract_names(str_address_list)

    # 更新地址映射，包含所有地址的合约名称
    address_map.update({address.get("address"): address.get("contract_name") for address in addresses})

    # 使用代理合约覆盖对应的实现合约名称
    for proxy_address, implementation_address in proxy_mapping.items():
        if implementation_address in address_map:
            address_map[proxy_address] = address_map[implementation_address]

    # Token
    addresses = (
        db.session.query(Tokens.address, Tokens.name, Tokens.symbol)
        .filter(
            Tokens.address.in_(wallet_address_list),
        )
        .all()
    )
    for address in addresses:
        address_map["0x" + address.address.hex()] = "{}: {} Token".format(address.name, address.symbol)

    # ENS
    if ens_client:
        addresses = ens_client.batch_get_address_ens(str_address_list)
        for key, value in addresses.items():
            address_map[key] = value

    # 手动Tag
    addresses = (
        db.session.query(StatisticsWalletAddresses.address, StatisticsWalletAddresses.tag)
        .filter(
            StatisticsWalletAddresses.address.in_(wallet_address_list),
            StatisticsWalletAddresses.tag != None,
        )
        .all()
    )

    for address in addresses:
        address_map[address.address] = address.tag

    return address_map


@cache.memoize(3600)
def get_ens_mapping(wallet_address_list):
    if ens_client:
        address_map = ens_client.batch_get_address_ens(wallet_address_list)

    return address_map
