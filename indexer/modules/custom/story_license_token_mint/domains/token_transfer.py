import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple, Union

from enumeration.token_type import TokenType
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.utils.abi import Event, bytes_to_hex_str
from indexer.utils.utils import ZERO_ADDRESS

logger = logging.getLogger(__name__)

deposit_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "dst", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

withdraw_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "src", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Withdrawal",
        "type": "event",
    }
)

transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
)

single_transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "id", "type": "uint256"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "TransferSingle",
        "type": "event",
    }
)

batch_transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "ids", "type": "uint256[]"},
            {"indexed": False, "name": "values", "type": "uint256[]"},
        ],
        "name": "TransferBatch",
        "type": "event",
    }
)

ip_register_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "implementation", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "chainId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "tokenContract", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "IPAccountRegistered",
        "type": "event",
    }
)

license_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "licenseTermsId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "licenseTemplate", "type": "address"},
            {"indexed": False, "internalType": "bytes", "name": "licenseTerms", "type": "bytes"},
        ],
        "name": "LicenseTermsRegistered",
        "type": "event",
    }
)

license_attach_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "caller", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "ipId", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "licenseTemplate", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "licenseTermsId", "type": "uint256"},
        ],
        "name": "LicenseTermsAttached",
        "type": "event",
    },
)

license_token_mint_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "caller", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "licensorIpId", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "licenseTemplate", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "licenseTermsId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "receiver", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "startLicenseTokenId", "type": "uint256"},
        ],
        "name": "LicenseTokensMinted",
        "type": "event",
    },
)

derivative_registered_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "caller", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "childIpId", "type": "address"},
            {"indexed": False, "internalType": "uint256[]", "name": "licenseTokenIds", "type": "uint256[]"},
            {"indexed": False, "internalType": "address[]", "name": "parentIpIds", "type": "address[]"},
            {"indexed": False, "internalType": "uint256[]", "name": "licenseTermsIds", "type": "uint256[]"},
            {"indexed": False, "internalType": "address", "name": "licenseTemplate", "type": "address"},
        ],
        "name": "DerivativeRegistered",
        "type": "event",
    },
)


@dataclass
class TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: Optional[int]
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int

    def to_specific_transfer(
        self,
    ) -> Union["ERC20TokenTransfer", "ERC721TokenTransfer", "ERC1155TokenTransfer"]:
        common_fields = {
            "transaction_hash": self.transaction_hash,
            "log_index": self.log_index,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "token_address": self.token_address,
            "block_number": self.block_number,
            "block_hash": self.block_hash,
            "block_timestamp": self.block_timestamp,
        }

        if self.token_type == TokenType.ERC20.value:
            return ERC20TokenTransfer(**common_fields, token_type=TokenType.ERC20.value, value=self.value)
        elif self.token_type == TokenType.ERC721.value:
            return ERC721TokenTransfer(**common_fields, token_type=TokenType.ERC721.value, token_id=self.value)
        elif self.token_type == TokenType.ERC1155.value and self.token_id is not None:
            return ERC1155TokenTransfer(
                **common_fields, token_type=TokenType.ERC1155.value, token_id=self.token_id, value=self.value
            )
        elif self.token_type == TokenType.ERC1155.value and self.token_id is None:
            return ERC20TokenTransfer(**common_fields, token_type=TokenType.ERC20.value, value=self.value)
        else:
            raise ValueError(f"Unsupported token type: {self.token_type}")


@dataclass
class ERC20TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class ERC721TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class ERC1155TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: int
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class StoryIpRegistered(Domain):
    transaction_hash: str
    log_index: int
    ip_account: str
    chain_id: int
    token_contract: str
    token_id: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class StoryLicenseTermsAttach(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    ip_id: str
    license_template: str
    license_terms_id: int
    block_number: int
    block_timestamp: int


@dataclass
class StoryLicenseTokenMinted(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    licensor_ip_id: str
    license_template: str
    license_terms_id: int
    amount: int
    receiver: str
    start_license_token_id: int
    block_number: int
    block_timestamp: int


@dataclass
class LicensePILRegister(Domain):
    transaction_hash: str
    log_index: int
    license_terms_id: int
    license_template: str
    transferable: bool
    royalty_policy: str
    default_minting_fee: int
    expiration: int
    commercial_use: bool
    commercial_attribution: bool
    commercializer_checker: str
    commercializer_checker_data: bytes
    commercial_rev_share: int
    commercial_rev_ceiling: int
    derivatives_allowed: bool
    derivatives_attribution: bool
    derivatives_approval: bool
    derivatives_reciprocal: bool
    derivative_rev_ceiling: int
    currency: str
    uri: str
    token_type: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class StoryDerivativeRegistered(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    child_ip_id: str
    license_token_ids: List[int]
    parent_ip_ids: List[str]
    license_terms_ids: List[int]
    license_template: str
    block_number: int
    block_timestamp: int


def handle_deposit_event(log: Log) -> List[TokenTransfer]:
    decode_data = deposit_event.decode_log(log)
    if decode_data is None:
        return []
    wallet_address = decode_data.get("dst").lower()
    value = decode_data.get("wad")
    token_type = TokenType.ERC20.value

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=ZERO_ADDRESS,
            to_address=wallet_address,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_withdraw_event(log: Log) -> List[TokenTransfer]:
    decode_data = withdraw_event.decode_log(log)
    if decode_data is None:
        return []
    wallet_address = decode_data.get("src").lower()
    value = decode_data.get("wad")
    token_type = TokenType.ERC20.value

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=wallet_address,
            to_address=ZERO_ADDRESS,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_event(log: Log) -> List[TokenTransfer]:
    decode_data = transfer_event.decode_log_ignore_indexed(log)

    from_address = decode_data.get("from").lower()
    to_address = decode_data.get("to").lower()
    value = decode_data.get("value")

    token_type = (
        TokenType.ERC721.value
        if log.topic3 or (log.topic1 is None and log.topic2 is None and log.topic3 is None)
        else TokenType.ERC20.value
    )

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_single_event(log: Log) -> List[TokenTransfer]:
    decode_data = single_transfer_event.decode_log(log)
    from_address = decode_data.get("from").lower()
    to_address = decode_data.get("to").lower()
    token_id = decode_data.get("id")
    value = decode_data.get("value")

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=token_id,
            value=value,
            token_type=TokenType.ERC1155.value,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_batch_event(log: Log) -> List[TokenTransfer]:
    decode_data = batch_transfer_event.decode_log(log)
    from_address = decode_data["from"].lower()
    to_address = decode_data["to"].lower()
    ids = decode_data["ids"]
    values = decode_data["values"]

    if len(ids) != len(values):
        logging.warning(f"ids length not equal to values length, log: {log}")
        return []

    token_amounts = defaultdict(int)
    for token_id, value in zip(ids, values):
        token_amounts[token_id] += value

    token_transfers = []
    for token_id, total_value in token_amounts.items():
        transfer = TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=token_id,
            value=total_value,
            token_type=TokenType.ERC1155.value,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
        token_transfers.append(transfer)

    return token_transfers


def handle_ip_register_event(log: Log) -> List[StoryIpRegistered]:
    decode_data = ip_register_event.decode_log_ignore_indexed(log)

    account = decode_data.get("account").lower()
    # imp_address = decode_data.get("implementation").lower()
    chain_id = decode_data.get("chainId")
    token_contract = decode_data.get("tokenContract").lower()
    token_id = decode_data.get("tokenId")

    token_type = "STORY"

    return [
        StoryIpRegistered(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            ip_account=account,
            chain_id=chain_id,
            token_contract=token_contract,
            token_id=token_id,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_license_attach_event(log: Log) -> List[StoryLicenseTermsAttach]:
    decode_data = license_attach_event.decode_log_ignore_indexed(log)

    caller = decode_data.get("caller").lower()
    ip_id = decode_data.get("ipId")
    license_template = decode_data.get("licenseTemplate").lower()
    license_terms_id = decode_data.get("licenseTermsId")

    return [
        StoryLicenseTermsAttach(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            caller=caller,
            ip_id=ip_id,
            license_template=license_template,
            license_terms_id=license_terms_id,
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_license_token_mint_event(log: Log) -> List[StoryLicenseTokenMinted]:
    decode_data = license_attach_event.decode_log_ignore_indexed(log)

    caller = decode_data.get("caller").lower()
    licensor_ip_id = decode_data.get("licensorIpId")
    license_template = decode_data.get("licenseTemplate").lower()
    license_terms_id = decode_data.get("licenseTermsId")
    amount = decode_data.get("amount")
    receiver = decode_data.get("receiver")
    start_license_token_id = decode_data.get("startLicenseTokenId")

    return [
        StoryLicenseTokenMinted(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            caller=caller,
            licensor_ip_id=licensor_ip_id,
            license_template=license_template,
            license_terms_id=license_terms_id,
            amount=amount,
            receiver=receiver,
            start_license_token_id=start_license_token_id,
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_license_event(log: Log) -> List[LicensePILRegister]:
    decode_data = license_event.decode_log(log)

    license_terms_id = decode_data.get("licenseTermsId")
    license_template = decode_data.get("licenseTemplate")
    license_terms = decode_data.get("licenseTerms")
    license_str = bytes_to_hex_str(license_terms)
    a = int(license_str[1282:1346])
    byte_sep = bytes.fromhex(license_str[1346 : 1346 + 2 * a])

    token_type = "STORY"

    return [
        LicensePILRegister(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            license_terms_id=license_terms_id,
            license_template=license_template,
            transferable=bool(license_str[129:130]),
            royalty_policy="0x" + license_str[154:194],
            default_minting_fee=int(license_str[194:258], 16),
            expiration=int(license_str[258:322], 16),
            commercial_use=bool(int(license_str[322:386])),
            commercial_attribution=bool(int(license_str[386:450])),
            commercializer_checker="0x" + license_str[474:514],
            commercializer_checker_data="0x" + license_str[1218:1258],
            commercial_rev_share=int(license_str[578:642], 16),
            commercial_rev_ceiling=int(license_str[642:706], 16),
            derivatives_allowed=bool(int(license_str[706:770])),
            derivatives_attribution=bool(int(license_str[770:834])),
            derivatives_approval=bool(int(license_str[834:898])),
            derivatives_reciprocal=bool(int(license_str[898:962])),
            derivative_rev_ceiling=int(license_str[962:1026], 16),
            currency="0x" + license_str[1050:1090],
            uri=byte_sep.decode("utf-8"),
            token_type=token_type,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_derivative_registered_event(log: Log) -> List[StoryDerivativeRegistered]:
    decode_data = derivative_registered_event.decode_log(log)

    caller = decode_data.get("caller")
    child_ip_id = decode_data.get("childIpId")
    license_token_ids = decode_data.get("licenseTokenIds")
    parent_ip_ids = decode_data.get("parentIpIds")
    license_terms_ids = decode_data.get("licenseTermsIds")
    license_template = decode_data.get("licenseTemplate")
    return [
        StoryDerivativeRegistered(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            caller=caller,
            child_ip_id=child_ip_id,
            license_token_ids=license_token_ids,
            parent_ip_ids=parent_ip_ids,
            license_terms_ids=license_terms_ids,
            license_template=license_template,
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]


def extract_transfer_from_log(log: Log) -> List[TokenTransfer]:
    token_transfers = []
    topic = log.topic0

    if topic == transfer_event.get_signature():
        token_transfers = handle_transfer_event(log)
    elif topic == deposit_event.get_signature():
        token_transfers = handle_deposit_event(log)
    elif topic == withdraw_event.get_signature():
        token_transfers = handle_withdraw_event(log)
    elif topic == single_transfer_event.get_signature():
        token_transfers = handle_transfer_single_event(log)
    elif topic == batch_transfer_event.get_signature():
        token_transfers = handle_transfer_batch_event(log)
    elif topic == register_event.get_signature():
        token_transfers = handle_register_event(log)

    return token_transfers


def extract_ip_register(log: Log) -> List[StoryIpRegistered]:
    story_data = []
    topic = log.topic0

    if topic == ip_register_event.get_signature():
        story_data = handle_ip_register_event(log)

    return story_data


def extract_license_register(log: Log) -> List[LicensePILRegister]:
    story_data = []
    topic = log.topic0

    if topic == license_event.get_signature():
        story_data = handle_license_event(log)

    return story_data


def extract_license_attach(log: Log) -> List[StoryLicenseTermsAttach]:
    story_data = []
    topic = log.topic0

    if topic == license_attach_event.get_signature():
        story_data = handle_license_attach_event(log)

    return story_data


def extract_license_token_mint(log: Log) -> List[StoryLicenseTokenMinted]:
    story_data = []
    topic = log.topic0

    if topic == license_token_mint_event.get_signature():
        story_data = handle_license_token_mint_event(log)

    return story_data


def extract_derivative_registered(log: Log) -> List[StoryDerivativeRegistered]:
    story_data = []
    topic = log.topic0

    if topic == derivative_registered_event.get_signature():
        story_data = handle_derivative_registered_event(log)

    return story_data
