from hemera.api.app.config import AppConfig, TokenConfiguration
from hemera.common.utils.exception_control import ErrorRollupError


class BridgeTransactionParser:
    def __init__(
        self,
        chain: str,
        rollup_type: str,
        withdrawal_expired_day: int,
        bridge_compatible: bool,
        token_configuration: TokenConfiguration = TokenConfiguration(
            native_token="ETH",
            dashboard_token="ETH",
            gas_fee_token="ETH",
        ),
    ):
        self.chain = chain
        self.rollup_type = rollup_type
        self.withdrawal_expired_day = withdrawal_expired_day
        self.bridge_compatible = bridge_compatible
        self.token_configuration = token_configuration

    def complete_format_tokens(self, tokens):
        for token in tokens:
            if token.icon_url is None:
                pass
                # token.icon_url = f"/images/empty-token-{self.chain}.png"

    @classmethod
    def init_from_config(cls, config: AppConfig):
        return cls(
            chain=config.chain,
            rollup_type=config.l2_config.rollup_type,
            withdrawal_expired_day=(
                int(config.l2_config.withdrawal_expired_day) if config.l2_config.withdrawal_expired_day else 0
            ),
            bridge_compatible=config.l2_config.bridge_compatible,
            token_configuration=config.token_configuration,
        )

    def parse_bridge_l1_to_l2_transaction(self, l1_to_l2_transaction, token_info):
        if self.rollup_type == "op":
            if self.chain == "mantle":
                return parse_mantle_bridge_l1_to_l2_transaction(l1_to_l2_transaction, token_info)
            else:
                transaction_json = parse_bedrock_bridge_l1_to_l2_transaction(
                    l1_to_l2_transaction,
                    token_info,
                    self.token_configuration.native_token,
                )
        elif self.rollup_type == "zk":
            if self.chain == "taiko":
                transaction_json = parse_taiko_bridge_l1_to_l2_transaction(l1_to_l2_transaction, token_info)
            else:
                transaction_json = parse_zk_bridge_l1_to_l2_transaction(l1_to_l2_transaction, token_info)
        elif self.rollup_type == "arbitrum":
            transaction_json = parse_bedrock_bridge_l1_to_l2_transaction(
                l1_to_l2_transaction, token_info, self.token_configuration.native_token
            )
        else:
            raise ErrorRollupError

        if self.bridge_compatible:
            handle_transaction_info_for_v1(l1_to_l2_transaction, transaction_json)
        return transaction_json

    def parse_bridge_l2_to_l1_transaction(self, l2_to_l1_transaction, token_info, finalized_block_number=None):
        if self.rollup_type == "op":
            if self.chain == "mantle":
                transaction_json = parse_mantle_bridge_l2_to_l1_transaction(l2_to_l1_transaction, token_info)
            else:
                transaction_json = parse_bedrock_bridge_l2_to_l1_transaction(
                    l2_to_l1_transaction,
                    token_info,
                    self.token_configuration.native_token,
                )
            transaction_json["status"] = determine_op_bedrock_withdrawal_state(
                transaction_json,
                finalized_block_number,
                self.withdrawal_expired_day,
            )
        elif self.rollup_type == "zk":
            if self.chain == "taiko":
                transaction_json = parse_taiko_bridge_l2_to_l1_transaction(l2_to_l1_transaction, token_info)
            else:
                transaction_json = parse_zk_bridge_l2_to_l1_transaction(l2_to_l1_transaction, token_info)
        elif self.rollup_type == "arbitrum":
            transaction_json = parse_bedrock_bridge_l2_to_l1_transaction(
                l2_to_l1_transaction, token_info, self.token_configuration.native_token
            )
        else:
            raise ErrorRollupError

        if self.bridge_compatible is not None:
            handle_transaction_info_for_v1(l2_to_l1_transaction, transaction_json)

        return transaction_json


def handle_transaction_info_for_v1(transaction, transaction_info):
    transaction_info["index"] = transaction["index"]
    if transaction_info["token_list"] is not None and len(transaction_info["token_list"]) > 0:
        token_info = transaction_info["token_list"][0]
        if token_info["token_type"] == "COIN":
            transaction_info["token_name"] = "ETH"
            transaction_info["l2_token_address"] = "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111"
            transaction_info["l1_token_address"] = "0x0000000000000000000000000000000000000000"
        else:
            transaction_info["token_name"] = token_info["token_name"]
            transaction_info["l2_token_address"] = transaction["l2_token_address"]
            transaction_info["l1_token_address"] = transaction["l1_token_address"]

        transaction_info["token_symbol"] = token_info["token_symbol"]
        transaction_info["value"] = token_info["value"]
        transaction_info["token_logo_url"] = token_info.get("token_logo_url")
        transaction_info["token_address"] = token_info.get("token_address")
        transaction_info["is_erc20"] = token_info.get("token_type") == "ERC20"
    transaction_info["amount"] = int(transaction["amount"]) if transaction["amount"] else 0
    transaction_info["l2_from_address"] = transaction["l2_from_address"]
    transaction_info["l1_from_address"] = transaction["l1_from_address"]
    transaction_info["l1_block_hash"] = transaction["l1_block_hash"]
    transaction_info["l2_block_hash"] = transaction["l2_block_hash"]


def determine_op_bedrock_withdrawal_state(transaction, finalized_block_number, expired_day=3):
    from datetime import datetime, timedelta, timezone

    current_time = datetime.now(timezone.utc)
    l1_proven_timestamp = None
    if transaction["l1_proven_block_timestamp"]:
        l1_proven_timestamp = datetime.fromisoformat(transaction["l1_proven_block_timestamp"])

    if finalized_block_number is None or finalized_block_number < transaction["l2_block_number"]:
        return 1  # Not Finalized
    elif transaction["l1_finalized_block_number"] is not None:
        return 5  # 'Relayed'
    elif transaction["l1_proven_block_number"] is None:
        return 2  # 'Ready to Prove'
    elif l1_proven_timestamp and current_time < l1_proven_timestamp + timedelta(days=expired_day):
        return 3  # 'In Challenge Period'
    else:
        return 4
    # ( l1_proven_timestamp and current_time >= l1_proven_timestamp + timedelta(days=expired_day) and transaction["l1_finalized_block_number"] is None)


def parse_taiko_bridge_l2_to_l1_transaction(transaction, token_info):
    transaction_dict = {
        "l2_transaction_hash": transaction["l2_transaction_hash"],
        "from_address": transaction["from_address"],
        "to_address": transaction["to_address"],
        "l2_block_number": transaction["l2_block_number"],
        "l2_block_timestamp": transaction["l2_block_timestamp"],
        "l1_block_number": transaction["l1_block_number"],
        "l1_block_timestamp": transaction["l1_block_timestamp"],
        "l1_transaction_hash": transaction["l1_transaction_hash"],
    }

    token_list = format_taiko_token_info(transaction, token_info)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_taiko_bridge_l1_to_l2_transaction(transaction, token_info):
    transaction_dict = transaction
    token_list = format_taiko_token_info(transaction, token_info)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_zk_bridge_l1_to_l2_transaction(transaction, token_info):
    transaction_dict = transaction
    token_list = format_linea_token_info(transaction, token_info)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_zk_bridge_l2_to_l1_transaction(transaction, token_info):
    transaction_dict = transaction

    token_list = format_linea_token_info(transaction, token_info)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_mantle_bridge_l1_to_l2_transaction(transaction, token_info):
    transaction_dict = transaction

    token_list = format_mantle_token_info(transaction, token_info)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_mantle_bridge_l2_to_l1_transaction(transaction, token_info):
    transaction_dict = transaction
    transaction_dict.update(
        {
            "l1_proven_txn_hash": transaction["l1_proven_transaction_hash"],
            "l1_finalized_block_number": transaction["l1_block_number"],
            "l1_finalized_block_timestamp": transaction["l1_block_timestamp"],
            "l1_finalized_transaction_hash": transaction["l1_transaction_hash"],
            "l1_finalized_txn_hash": transaction["l1_transaction_hash"],
        }
    )

    token_list = format_mantle_token_info(transaction, token_info, "L2")
    transaction_dict["token_list"] = token_list

    return transaction_dict


def parse_bedrock_bridge_l1_to_l2_transaction(transaction, token_info, native_token="ETH"):
    transaction_dict = transaction
    token_list = format_bedrock_token_info(transaction, token_info, native_token)
    transaction_dict["token_list"] = token_list
    return transaction_dict


def parse_bedrock_bridge_l2_to_l1_transaction(transaction, token_info, native_token="ETH"):
    transaction_dict = transaction
    transaction_dict.update(
        {
            "l1_proven_txn_hash": transaction["l1_proven_transaction_hash"],
            "l1_finalized_block_number": transaction["l1_block_number"],
            "l1_finalized_block_timestamp": transaction["l1_block_timestamp"],
            "l1_finalized_transaction_hash": transaction["l1_transaction_hash"],
            "l1_finalized_txn_hash": transaction["l1_transaction_hash"],
        }
    )

    token_list = format_bedrock_token_info(transaction, token_info, native_token)
    transaction_dict["token_list"] = token_list

    return transaction_dict


def format_value(amount, decimals=18):
    """Function to format the value, handling decimal places."""
    formatted_value = f"{amount / 10 ** decimals:.6f}".rstrip("0").rstrip(".")
    return formatted_value if formatted_value else "0"


def format_taiko_token_info(transaction, token_info):
    """Extract and format token information from a Taiko transaction."""
    token_list = []
    if transaction["extra_info"].get("token"):
        token = transaction["extra_info"]["token"]
        token_dict = {
            "token_name": token["ctoken"]["name"],
            "token_symbol": token["ctoken"]["symbol"],
            "token_logo_url": token_info["icon_url"],
            "token_type": token["type"],
            "token_address": token_info["address"],
            "value": (
                format_value(int(token["amount"]), int(token["ctoken"]["decimals"])) if token["type"] == "ERC20" else ""
            ),
        }

        if token["type"] == "ERC721":
            token_dict["token_ids"] = token["tokenIds"]
            token_dict["value"] = str(len(token["tokenIds"]))
        elif token["type"] == "ERC1155":
            token_dict["amounts"] = token["amounts"]
            token_dict["token_ids"] = token["tokenIds"]
            token_dict["value"] = str(sum(int(item) for item in token["amounts"]))

        token_list.append(token_dict)

    if transaction["amount"] > 0:
        token_list.append(
            {
                "token_name": "ETH",
                "token_symbol": "ETH",
                "token_type": "COIN",
                "value": format_value(transaction["amount"]),
            }
        )

    return token_list


def format_mantle_token_info(transaction, token_info, bridge_type="L1"):
    """Extract and format token information from a transaction."""
    token_list = []

    token_defaults = {
        "0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000": {
            "token_name": "Mantle",
            "token_symbol": "MNT",
            "token_type": "COIN",
        },
        "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111": {
            "token_name": "ETH",
            "token_symbol": "ETH",
            "token_type": "COIN",
        },
    }

    if token_info:
        address = token_info.get("address")
        if address in token_defaults:
            token_data = token_defaults[address]
            token_list.append(
                {
                    "token_name": token_data["token_name"],
                    "token_symbol": token_data["token_symbol"],
                    "token_type": token_data["token_type"],
                    "value": format_value(transaction["amount"], 18),
                }
            )
        else:
            token_list.append(
                {
                    "token_name": token_info["name"],
                    "token_symbol": token_info["symbol"],
                    "token_type": token_info["token_type"],
                    "token_logo_url": token_info["icon_url"],
                    "token_address": token_info["address"],
                    "value": format_value(transaction["amount"], token_info["decimals"] or 0),
                }
            )
    else:
        if bridge_type == "L1":
            token_list.append(
                {
                    "token_name": "",
                    "token_symbol": "",
                    "token_type": None,
                    "value": "Tss Reward",
                }
            )
        else:
            token_list.append(
                {
                    "token_name": "ETH",
                    "token_symbol": "ETH",
                    "token_type": "COIN",
                    "value": format_value(transaction["amount"], 18),
                }
            )

    return token_list


def format_linea_token_info(transaction, token_info):
    token_list = []
    if token_info:
        token_list.append(
            {
                "token_name": token_info["name"],
                "token_symbol": token_info["symbol"],
                "token_type": token_info["token_type"],
                "token_logo_url": token_info["icon_url"],
                "token_address": token_info["address"],
                "value": format_value(transaction["amount"], token_info.get("decimals", 18)),
            }
        )
    else:
        token_list.append(
            {
                "token_name": "ETH",
                "token_symbol": "ETH",
                "token_type": "COIN",
                "value": format_value(transaction["amount"]),
            }
        )

    return token_list


def format_bedrock_token_info(transaction, token_info, native_token="ETH"):
    token_list = []
    if token_info:
        token_name = (
            "ETH" if token_info["address"] == "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111" else token_info["name"]
        )
        token_type = "COIN" if token_name == "ETH" else token_info["token_type"]
        token_list.append(
            {
                "token_name": token_name,
                "token_symbol": token_info["symbol"],
                "token_type": token_type,
                "token_logo_url": token_info.get("icon_url", ""),
                "token_address": token_info["address"],
                "value": format_value(transaction["amount"], token_info.get("decimals", 18)),
            }
        )
    else:
        token_list.append(
            {
                "token_name": native_token,
                "token_symbol": native_token,
                "token_type": "COIN",
                "value": format_value(transaction["amount"]),
            }
        )

    return token_list
