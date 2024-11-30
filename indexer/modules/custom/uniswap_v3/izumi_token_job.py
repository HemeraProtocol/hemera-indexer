import logging
import queue

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from common.utils.web3_utils import ZERO_ADDRESS
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.token_transfer import ERC721TokenTransfer
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    IzumiToken,
    IzumiTokenCurrentState,
    IzumiTokenState,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.collection_utils import distinct_collections_by_group
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)

from indexer.modules.custom.uniswap_v3.izumi_abi import (
    DECREASE_LIQUIDITY_EVENT,
    INCREASE_LIQUIDITY_EVENT,
    OWNER_OF_FUNCTION,
    POSITIONS_FUNCTION,
    UPDATE_LIQUIDITY_EVENT,
)

liquidity_event_list = [INCREASE_LIQUIDITY_EVENT, UPDATE_LIQUIDITY_EVENT, DECREASE_LIQUIDITY_EVENT]
LIQUIDITY_EVENT_TOPIC0_DICT = {e.get_signature(): e for e in liquidity_event_list}


class ExportIzumiTokensJob(FilterTransactionDataJob):
    dependency_types = [Log, ERC721TokenTransfer, Block]
    output_types = [IzumiToken, IzumiTokenState, IzumiTokenCurrentState]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._service = kwargs["config"].get("db_service")
        self._multicall_helper = MultiCallHelper(
            self._web3, {"batch_size": kwargs["batch_size"], "multicall": True, "max_workers": kwargs["max_workers"]}
        )

        config = kwargs["config"]["izumi_pool_job"]
        self._position_token_address = config.get("position_token_address").lower()
        self._factory_address = config.get("factory_address").lower()

        self._exist_pools = get_exist_pools(self._service, self._position_token_address)
        self._exist_token_ids = get_exist_token_ids(self._service, self._position_token_address)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[self._factory_address],
                ),
                TopicSpecification(addresses=[self._position_token_address]),
            ]
        )

    def _collect(self, **kwargs):
        blocks = self._data_buff[Block.type()]
        erc721_token_transfers = self._data_buff[ERC721TokenTransfer.type()]
        logs = self._data_buff[Log.type()]

        self._block_infos = {}
        for data in blocks:
            self._block_infos[data.number] = data.timestamp

        # collect the nft_ids which were minted or burned
        mint_token_ids, burn_token_ids, all_token_dict = extract_changed_tokens(
            erc721_token_transfers, self._position_token_address
        )
        token_id_liquidity_records = extract_liquidity_logs(logs, self._position_token_address)

        # tokens_to_update_states -> [{"token_id": "xxx", "block_number": xxx}]
        # tokens_to_update_info set((token_id, block_number), (token_id,block_number))
        tokens_to_update_states, tokens_to_update_info = gather_collect_infos(
            all_token_dict,
            token_id_liquidity_records,
            burn_token_ids,
            self._exist_token_ids,
        )
        # call owners
        token_id_block_owner = self.get_token_id_block_owner(
            tokens_to_update_states,
            self._position_token_address,
        )

        # call positions
        # token_infos -> [{"token_id": "111", "block_number": 222, "liquidity": 333, "tickerLower", "tickerUpper","poolId"}]
        # Need to fill pool address to token_infos
        token_id_block_positions = self.get_token_id_block_position(
            tokens_to_update_states,
            self._position_token_address,
            self._exist_pools,
        )

        # filter the info which call pool needed
        update_exist_tokens, new_nft_info = get_new_nfts(
            token_id_block_positions,
            tokens_to_update_info,
            self._position_token_address,
            self._block_infos,
        )
        self._exist_token_ids.update(update_exist_tokens)

        for data in new_nft_info:
            self._collect_item(IzumiToken.type(), data)
            self._exist_token_ids[data.token_id] = data.pool_address
        token_result, current_statuses = parse_token_records(
            self._position_token_address,
            self._exist_token_ids,
            token_id_block_owner,
            token_id_block_positions,
            self._block_infos,
        )

        for data in token_result:
            self._collect_item(IzumiTokenState.type(), data)
        for data in current_statuses:
            self._collect_item(IzumiTokenCurrentState.type(), data)

        for token_id, block_number in burn_token_ids.items():
            self._collect_item(
                IzumiTokenState.type(),
                IzumiTokenState(
                    position_token_address=self._position_token_address,
                    pool_address=self._exist_token_ids.get(token_id, ""),
                    token_id=token_id,
                    wallet_address=ZERO_ADDRESS,
                    liquidity=0,
                    block_number=block_number,
                    block_timestamp=self._block_infos[block_number],
                ),
            )
            self._collect_item(
                IzumiTokenCurrentState.type(),
                IzumiTokenCurrentState(
                    position_token_address=self._position_token_address,
                    pool_address=self._exist_token_ids.get(token_id, ""),
                    token_id=token_id,
                    wallet_address=ZERO_ADDRESS,
                    liquidity=0,
                    block_number=block_number,
                    block_timestamp=self._block_infos[block_number],
                ),
            )

        self._data_buff[IzumiTokenCurrentState.type()] = distinct_collections_by_group(
            self._data_buff[IzumiTokenCurrentState.type()], ["position_token_address", "token_id"], "block_number"
        )

        self._block_infos = {}

    def _process(self, **kwargs):
        self._data_buff[IzumiToken.type()].sort(key=lambda x: x.block_number)
        self._data_buff[IzumiTokenState.type()].sort(key=lambda x: x.block_number)
        self._data_buff[IzumiTokenCurrentState.type()].sort(key=lambda x: x.block_number)

        
    def get_token_id_block_owner(self, tokens_to_update_states, position_token_address):
        owner_of_calls = []
        for token in tokens_to_update_states:
            token_id = token["token_id"]
            block_number = token["block_number"]
            owner_of_calls.append(
                Call(
                    target=position_token_address,
                    function_abi=OWNER_OF_FUNCTION,
                    parameters=[token_id],
                    block_number=block_number,
                )
            )
        self._multicall_helper.execute_calls(owner_of_calls)

        token_id_block_owner = {}
        for call in owner_of_calls:
            token_id = call.parameters[0]
            if token_id not in token_id_block_owner:
                token_id_block_owner[token_id] = {}
            token_id_block_owner[token_id][call.block_number] = call.returns["owner"]
        return token_id_block_owner


    def get_token_id_block_position(self, tokens_to_update_states, position_token_address, exist_pools):
        position_calls = []
        for token in tokens_to_update_states:
            token_id = token["token_id"]
            block_number = token["block_number"]
            position_calls.append(
                Call(
                    target=position_token_address,
                    function_abi=POSITIONS_FUNCTION,
                    parameters=[token_id],
                    block_number=block_number
                )
            )
        self._multicall_helper.execute_calls(position_calls)

        token_id_block_positions = []
        for call in position_calls:
            token["token_id"] = call.parameters[0]
            token["block_number"] = call.block_number

            token["tickLower"] = call.returns["leftPt"]
            token["tickUpper"] = call.returns["rightPt"]
            token["liquidity"] = call.returns["liquidity"]
            token["feeGrowthInside0LastX128"] = call.returns["lastFeeScaleX_128"]
            token["feeGrowthInside1LastX128"] = call.returns["lastFeeScaleY_128"]
            token["tokensOwed0"] = call.returns["remainTokenX"]
            token["tokensOwed1"] = call.returns["remainTokenY"]
            token["poolId"] = call.returns["poolId"]

            if token["poolId"] in exist_pools:
                token["token0"] = exist_pools[token["poolId"]]["token0_address"]
                token["token1"] = exist_pools[token["poolId"]]["token1_address"]
                token["fee"] = exist_pools[token["poolId"]]["fee"]
                token["pool_address"] = exist_pools[token["poolId"]]["pool_address"]

            # token["nonce"] = decoded_data[0]
            # token["operator"] = decoded_data[1]
            # token["token0"] = decoded_data[2]
            # token["token1"] = decoded_data[3]
            # token["fee"] = decoded_data[4]

            token_id_block_positions.append(token)
        return token_id_block_positions


def parse_token_records(
    position_token_address, token_pool_dict, token_id_block_owner, token_id_block_positions, block_info
):
    token_result = []
    token_block_dict = {}

    for data in token_id_block_positions:
        block_number = data["block_number"]
        token_id = data["token_id"]
        liquidity = data["liquidity"]

        if token_id not in token_pool_dict:
            continue

        token_block_dict[token_id] = max(token_block_dict.get(token_id, block_number), block_number)

        address = token_id_block_owner[token_id][block_number]
        pool_address = token_pool_dict[token_id]

        token_result.append(
            IzumiTokenState(
                position_token_address=position_token_address,
                pool_address=pool_address,
                token_id=token_id,
                wallet_address=address,
                liquidity=liquidity,
                block_number=block_number,
                block_timestamp=block_info[block_number],
            )
        )

    current_statuses = []
    for token_id, max_block_number in token_block_dict.items():
        max_block_data = next(
            data
            for data in token_id_block_positions
            if data["token_id"] == token_id and data["block_number"] == max_block_number
        )
        address = token_id_block_owner[token_id][max_block_number]
        pool_address = token_pool_dict[token_id]

        current_statuses.append(
            IzumiTokenCurrentState(
                position_token_address=position_token_address,
                token_id=token_id,
                pool_address=pool_address,
                wallet_address=address,
                liquidity=max_block_data["liquidity"],
                block_number=max_block_number,
                block_timestamp=block_info[max_block_number],
            )
        )
    return token_result, current_statuses


def gather_collect_infos(all_token_dict, token_id_block, burn_token_ids, exist_token_ids):
    seen = set()
    for token_id, blocks in all_token_dict.items():
        for block_number, to_address in blocks.items():
            seen.add((token_id, block_number))
    for token_id, blocks in token_id_block.items():
        for block_number, to_address in blocks.items():
            seen.add((token_id, block_number))

    tokens_to_update_states = []
    tokens_to_update_info = set()
    for item in seen:
        token_id = item[0]
        block_number = item[1]

        # If token is not burned or token burned after this block_number
        # we need to get state for this block
        if token_id not in burn_token_ids or burn_token_ids[token_id] > block_number:
            tokens_to_update_states.append(
                {
                    "token_id": token_id,
                    "block_number": block_number,
                }
            )

        # If token id not in
        if token_id not in exist_token_ids:
            tokens_to_update_info.add((token_id, block_number))
    return tokens_to_update_states, tokens_to_update_info


def get_new_nfts(
    token_id_block_positions,
    tokens_to_update_info,
    position_token_address,
    block_infos,
):
    result = []
    need_collect_pool_tokens = []
    for position in token_id_block_positions:
        token_id = position["token_id"]
        block_number = position["block_number"]
        if (token_id, block_number) in tokens_to_update_info:
            need_collect_pool_tokens.append(position)

    # get new nft_id info
    update_exist_tokens = {}
    seen = set()

    print(need_collect_pool_tokens)

    for data in need_collect_pool_tokens:
        token_id = data["token_id"]
        if (position_token_address, token_id) in seen:
            continue
        seen.add((position_token_address, token_id))

        # Skip non exist pool
        if "pool_address" not in data:
            continue
        pool_address = data["pool_address"]
        update_exist_tokens[token_id] = pool_address

        result.append(
            IzumiToken(
                position_token_address=position_token_address,
                token_id=token_id,
                pool_address=pool_address,
                tick_lower=data["tickLower"],
                tick_upper=data["tickUpper"],
                fee=data["fee"],
                block_number=data["block_number"],
                block_timestamp=block_infos[data["block_number"]],
            )
        )
    return update_exist_tokens, result


def get_exist_token_ids(db_service, position_token_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Tokens.token_id, UniswapV3Tokens.pool_address)
            .filter(
                UniswapV3Tokens.pool_address != None,
                UniswapV3Tokens.position_token_address == hex_str_to_bytes(position_token_address),
            )
            .all()
        )
        token_id_pool_dict = {}
        if result is not None:
            for item in result:
                token_id = (item.token_id,)
                token_id_pool_dict[token_id] = bytes_to_hex_str(item.pool_address)
    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return token_id_pool_dict


def extract_changed_tokens(token_transfers, position_token_address):
    mint_tokens_dict = {}
    burn_tokens_dict = {}
    all_tokens_dict = {}
    sorted_transfers = sorted(token_transfers, key=lambda x: (x.block_number, x.log_index))

    for transfer in sorted_transfers:
        token_address = transfer.token_address
        if token_address != position_token_address:
            continue
        token_id = transfer.token_id
        block_number = transfer.block_number
        to_address = transfer.to_address
        from_address = transfer.from_address

        if token_id not in all_tokens_dict:
            all_tokens_dict[token_id] = {}
        all_tokens_dict[token_id][block_number] = to_address

        if to_address == ZERO_ADDRESS:
            burn_tokens_dict[token_id] = block_number
        elif from_address == ZERO_ADDRESS:
            mint_tokens_dict[token_id] = block_number

    return mint_tokens_dict, burn_tokens_dict, all_tokens_dict


def extract_liquidity_logs(logs, position_token_address):
    token_id_block = {}

    for log in logs:
        if log.address != position_token_address:
            continue

        if log.topic0 in LIQUIDITY_EVENT_TOPIC0_DICT:
            event = LIQUIDITY_EVENT_TOPIC0_DICT.get(log.topic0)
            if event:
                log_decoded_data = event.decode_log(log)
                token_id = log_decoded_data["nftId"]
                token_id_block.setdefault(token_id, {})[log.block_number] = log.topic0
    return token_id_block


def get_exist_pools(db_service, position_token_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Pools)
            .filter(
                UniswapV3Pools.position_token_address == hex_str_to_bytes(position_token_address),
                UniswapV3Pools.pool_id != None,
            )
            .all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = bytes_to_hex_str(item.pool_address)
                history_pools[item.pool_id] = {
                    "pool_address": pool_key,
                    "position_token_address": bytes_to_hex_str(item.position_token_address),
                    "token0_address": bytes_to_hex_str(item.token0_address),
                    "token1_address": bytes_to_hex_str(item.token1_address),
                    "fee": item.fee,
                    "tick_spacing": item.tick_spacing,
                    "block_number": item.block_number,
                    "pool_id": item.pool_id,
                }

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return history_pools
