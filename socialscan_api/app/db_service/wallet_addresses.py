import binascii

from common.models import db
from common.models.contracts import Contracts
from common.models.tokens import Tokens
from common.models.wallet_addresses import WalletAddresses
from common.models.wallet_addresses import WalletAddresses as ExplorerWalletAddresses
from common.utils.config import get_config
from socialscan_api.app.cache import cache
from socialscan_api.app.contract.contract_verify import get_contract_names
from socialscan_api.app.ens.ens import ENSClient

app_config = get_config()

if app_config.ens_service is not None and app_config.ens_service != "":
    ens_client = ENSClient(app_config.ens_service)
else:
    ens_client = None

token_address_transfers_type_column_dict = {
    "tokentxns": WalletAddresses.erc20_transfer_cnt,
    "tokentxns-nft": WalletAddresses.erc721_transfer_cnt,
    "tokentxns-nft1155": WalletAddresses.erc1155_transfer_cnt,
}


def type_to_stats_column(type):
    return token_address_transfers_type_column_dict[type]


def get_token_txn_cnt_by_address(token_type, address):
    result = (
        db.session.query(WalletAddresses)
        .with_entities(type_to_stats_column(token_type))
        .filter(WalletAddresses.address == address)
        .first()
    )

    return result


def get_txn_cnt_by_address(address):
    result = (
        db.session.query(WalletAddresses)
        .with_entities(WalletAddresses.txn_cnt)
        .filter(WalletAddresses.address == address)
        .first()
    )
    return result


@cache.memoize(3600)
def get_address_display_mapping(wallet_address_list):
    # filter not valid address
    wallet_address_list = [address for address in wallet_address_list if address]
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
    addresses = get_contract_names(all_addresses)

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
            Tokens.address.in_([binascii.unhexlify(token_address[2:]) for token_address in wallet_address_list]),
        )
        .all()
    )
    for address in addresses:
        address_map["0x" + address.address.hex()] = "{}: {} Token".format(address.name, address.symbol)

    # ENS
    if ens_client:
        addresses = ens_client.batch_get_address_ens(wallet_address_list)
        for key, value in addresses.items():
            address_map[key] = value
    else:
        addresses = (
            db.session.query(WalletAddresses.address, WalletAddresses.ens_name)
            .filter(
                WalletAddresses.address.in_(wallet_address_list),
                WalletAddresses.ens_name != None,
            )
            .all()
        )

        for address in addresses:
            address_map[address.address] = address.ens_name

    # 手动Tag
    addresses = (
        db.session.query(ExplorerWalletAddresses.address, ExplorerWalletAddresses.tag)
        .filter(
            ExplorerWalletAddresses.address.in_(wallet_address_list),
            ExplorerWalletAddresses.tag != None,
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
    else:
        addresses = (
            db.session.query(WalletAddresses)
            .filter(
                WalletAddresses.address.in_(wallet_address_list),
                WalletAddresses.ens_name is not None,
            )
            .all()
        )
        address_map = {}
        for address in addresses:
            address_map[address.address] = address.ens_name
    return address_map
