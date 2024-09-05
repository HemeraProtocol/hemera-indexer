import configparser
import json
import logging
import os
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import fields

import eth_abi
from web3 import Web3

from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3 import constants, util
from indexer.modules.custom.uniswap_v3.constants import UNISWAP_V3_ABI
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import (
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
    UniswapV3Pool,
    UniswapV3TokenCollectFee,
    UniswapV3TokenUpdateLiquidity,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_TOKENS.value


class UniswapV3TokenJob(FilterTransactionDataJob):
    dependency_types = [Log, UniswapV3Pool]
    output_types = [UniswapV3Token, UniswapV3TokenDetail, UniswapV3TokenCurrentStatus, UniswapV3TokenUpdateLiquidity,
                    UniswapV3TokenCollectFee]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._service = kwargs["config"].get("db_service")
        self._load_config("config.ini", self._chain_id)
        self._abi_list = UNISWAP_V3_ABI
        self._liquidity_token_id_blocks = queue.Queue()
        self._exist_token_ids = get_exist_token_ids(self._service, self._nft_address)
        self._exist_pool_infos = get_exist_pools(self._service, self._nft_address)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)
        chain_id_str = str(chain_id)
        try:
            chain_config = config[chain_id_str]
        except KeyError:
            return
        try:
            self._nft_address = chain_config.get("nft_address").lower()
            self._factory_address = chain_config.get("factory_address").lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._nft_address]),
            ]
        )

    def _collect(self, **kwargs):
        # get new pool
        collected_pools = self._data_buff[UniswapV3Pool.type()]
        for data in collected_pools:
            self._exist_pool_infos[data.pool_address] = data
        info_pool_dict = {}
        for data in self._exist_pool_infos.values():
            key = (data.token0_address, data.token1_address, data.fee)
            info_pool_dict[key] = data.pool_address

        # collect token_id's data
        logs = self._data_buff[Log.type()]
        early_token_id_data = {}
        need_collect_token_id_data = []
        need_collect_token_id_set = set()
        for log in logs:
            topic0 = log.topic0
            address = log.address
            block_number = log.block_number
            block_timestamp = log.block_timestamp
            if address != self._nft_address:
                continue
            if topic0 == constants.TRANSFER_TOPIC0:
                token_id_hex = log.topic3
            elif topic0 == constants.UNISWAP_V3_ADD_LIQUIDITY_TOPIC0 or topic0 == constants.UNISWAP_V3_REMOVE_LIQUIDITY_TOPIC0:
                token_id_hex = log.topic1
            else:
                continue
            token_id = util.parse_hex_to_uint256(token_id_hex)
            key = (token_id, block_number, block_timestamp)
            data = {
                "token_id": token_id,
                "block_number": block_number,
                "block_timestamp": block_timestamp
            }
            if key not in need_collect_token_id_set:
                need_collect_token_id_data.append(data)
                need_collect_token_id_set.add(key)
            if token_id in early_token_id_data:
                early_block_number, early_block_timestamp = early_token_id_data[token_id]
                if block_number < early_block_number:
                    early_token_id_data[token_id] = (block_number, block_timestamp)
            else:
                early_token_id_data[token_id] = (block_number, block_timestamp)

        if len(need_collect_token_id_data) == 0:
            return

        # call owners
        owner_info = owner_rpc_requests(self._web3, self._batch_web3_provider.make_request, need_collect_token_id_data,
                                        self._nft_address, self._is_batch, self._abi_list, self._batch_size,
                                        self._max_worker)
        # call positions
        token_infos = positions_rpc_requests(
            self._web3,
            self._batch_web3_provider.make_request,
            owner_info,
            self._nft_address,
            self._is_batch,
            self._abi_list,
            self._batch_size,
            self._max_worker,
        )
        token_id_current_status = {}
        for data in token_infos:
            token_id = data["token_id"]
            block_number = data["block_number"]
            block_timestamp = data["block_timestamp"]
            if token_id not in self._exist_token_ids:
                # need save token_info
                fee = data["fee"]
                key = (data["token0"], data["token1"], fee)
                pool_address = info_pool_dict[key]
                tick_lower = data["tickLower"],
                tick_upper = data["tickUpper"],
                self._collect_item(UniswapV3Token.type(), UniswapV3Token(nft_address=self._nft_address,
                                                                         token_id=token_id,
                                                                         pool_address=pool_address,
                                                                         tick_lower=tick_lower, tick_upper=tick_upper,
                                                                         fee=fee, block_number=block_number,
                                                                         block_timestamp=block_timestamp))
                self._exist_token_ids[token_id] = pool_address
            else:
                pool_address = self._exist_token_ids[token_id]
            wallet_address = constants.ZERO_ADDRESS
            if "owner" in data:
                wallet_address = data["owner"]
            liquidity = 0
            if "liquidity" in data:
                liquidity = data["liquidity"]
            detail = UniswapV3TokenDetail(
                nft_address=self._nft_address,
                pool_address=pool_address,
                token_id=token_id,
                wallet_address=wallet_address,
                liquidity=liquidity,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )
            self._collect_item(UniswapV3TokenDetail.type(), detail)
            token_id = detail.token_id
            if token_id not in token_id_current_status or block_number > token_id_current_status[token_id].block_number:
                token_id_current_status[token_id] = create_token_status(detail)

        for data in token_id_current_status.values():
            self._collect_item(UniswapV3TokenCurrentStatus.type(), data)

        # collect fee and liquidity
        for log in logs:
            topic0 = log.topic0
            if topic0 == constants.UNISWAP_V3_REMOVE_LIQUIDITY_TOPIC0:
                token_id = util.parse_hex_to_uint256(log.topic1)
                pool_address = self._exist_token_ids[token_id]
                pool_info = self._exist_pool_infos[pool_address]
                liquidity_hex, amount0_hex, amount1_hex = split_hex_string(log.data)
                self._collect_item(UniswapV3TokenUpdateLiquidity.type(), UniswapV3TokenUpdateLiquidity(
                    nft_address=self._nft_address, token_id=token_id,
                    action_type=constants.DECREASE_TYPE, transaction_hash=log.transaction_hash,
                    liquidity=util.parse_hex_to_uint256(liquidity_hex), amount0=util.parse_hex_to_uint256(amount0_hex),
                    amount1=util.parse_hex_to_uint256(amount1_hex), pool_address=pool_address,
                    token0_address=pool_info.token0_address, token1_address=pool_info.token1_address,
                    log_index=log.log_index, block_number=log.block_number, block_timestamp=log.block_timestamp
                ))
            elif topic0 == constants.UNISWAP_V3_ADD_LIQUIDITY_TOPIC0:
                token_id = util.parse_hex_to_uint256(log.topic1)
                pool_address = self._exist_token_ids[token_id]
                pool_info = self._exist_pool_infos[pool_address]
                liquidity_hex, amount0_hex, amount1_hex = split_hex_string(log.data)
                self._collect_item(UniswapV3TokenUpdateLiquidity.type(), UniswapV3TokenUpdateLiquidity(
                    nft_address=self._nft_address, token_id=token_id,
                    action_type=constants.INCREASE_TYPE, transaction_hash=log.transaction_hash,
                    liquidity=util.parse_hex_to_uint256(liquidity_hex), amount0=util.parse_hex_to_uint256(amount0_hex),
                    amount1=util.parse_hex_to_uint256(amount1_hex), pool_address=pool_address,
                    token0_address=pool_info.token0_address, token1_address=pool_info.token1_address,
                    log_index=log.log_index, block_number=log.block_number, block_timestamp=log.block_timestamp
                ))
            elif topic0 == constants.UNISWAP_V3_TOKEN_COLLECT_FEE_TOPIC0:
                token_id = util.parse_hex_to_uint256(log.topic1)
                pool_address = self._exist_token_ids[token_id]
                pool_info = self._exist_pool_infos[pool_address]
                recipient_hex, amount0_hex, amount1_hex = split_hex_string(log.data)
                self._collect_item(UniswapV3TokenCollectFee.type(), UniswapV3TokenCollectFee(
                    nft_address=self._nft_address, token_id=token_id,
                    transaction_hash=log.transaction_hash, recipient=util.parse_hex_to_address(recipient_hex),
                    amount0=util.parse_hex_to_uint256(amount0_hex), amount1=util.parse_hex_to_uint256(amount1_hex),
                    pool_address=pool_address,
                    token0_address=pool_info.token0_address, token1_address=pool_info.token1_address,
                    log_index=log.log_index, block_number=log.block_number, block_timestamp=log.block_timestamp
                ))
            else:
                continue

    def _process(self, **kwargs):
        self._data_buff[UniswapV3Token.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3TokenDetail.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3TokenCurrentStatus.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3TokenUpdateLiquidity.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3TokenCollectFee.type()].sort(key=lambda x: x.block_number)


def get_exist_pools(db_service, nft_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Pools).filter(UniswapV3Pools.nft_address == bytes.fromhex(nft_address[2:])).all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = "0x" + item.pool_address.hex()
                history_pools[pool_key] = UniswapV3Pool(
                    pool_address=pool_key,
                    nft_address="0x" + item.nft_address.hex(),
                    factory_address="0x" + item.factory_address.hex(),
                    token0_address="0x" + item.token0_address.hex(),
                    token1_address="0x" + item.token1_address.hex(),
                    fee=item.fee,
                    tick_spacing=item.tick_spacing,
                    block_number=item.block_number,
                    block_timestamp=item.block_timestamp
                )
    except Exception as e:
        raise e
    finally:
        session.close()

    return history_pools


def get_exist_token_ids(db_service, nft_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Tokens.token_id, UniswapV3Tokens.pool_address)
            .filter(
                UniswapV3Tokens.nft_address == bytes.fromhex(nft_address[2:]),
            )
            .all()
        )
        history_token = {}
        if result is not None:
            for item in result:
                token_id = item.token_id
                history_token[token_id] = "0x" + item.pool_address.hex()
    except Exception as e:
        raise e
    finally:
        session.close()
    return history_token


def build_token_id_method_data(web3, token_ids, nft_address, fn, abi_list):
    parameters = []
    contract = web3.eth.contract(address=Web3.to_checksum_address(nft_address), abi=abi_list)

    for idx, token in enumerate(token_ids):
        token_data = {
            "request_id": idx,
            "param_to": nft_address,
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)

        try:
            # Encode the ABI for the specific token_id
            data = contract.encodeABI(fn_name=fn, args=[token["token_id"]])
            token["param_data"] = data
        except Exception as e:
            logger.error(
                f"Encoding token id {token['token_id']} for function {fn} failed. "
                f"NFT address: {nft_address}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters


def positions_rpc_requests(web3, make_requests, requests, nft_address, is_batch, abi_list, batch_size, max_workers):
    if len(requests) == 0:
        return []

    fn_name = "positions"
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_token_id_method_data(web3, requests, nft_address, fn_name, abi_list)
    token_name_rpc = list(generate_eth_call_json_rpc(parameters))

    def process_batch(batch):
        if is_batch:
            response = make_requests(params=json.dumps(batch))
        else:
            response = [make_requests(params=json.dumps(batch[0]))]

        token_infos = []
        for data in list(zip_rpc_response(parameters, response)):
            result = rpc_response_to_result(data[1])
            token = data[0]
            value = result[2:] if result is not None else None
            try:
                decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
                token["nonce"] = decoded_data[0]
                token["operator"] = decoded_data[1]
                token["token0"] = decoded_data[2]
                token["token1"] = decoded_data[3]
                token["fee"] = decoded_data[4]
                token["tickLower"] = decoded_data[5]
                token["tickUpper"] = decoded_data[6]
                token["liquidity"] = decoded_data[7]
                token["feeGrowthInside0LastX128"] = decoded_data[8]
                token["feeGrowthInside1LastX128"] = decoded_data[9]
                token["tokensOwed0"] = decoded_data[10]
                token["tokensOwed1"] = decoded_data[11]

            except Exception as e:
                logger.error(
                    f"Decoding positions failed. "
                    f"token: {token}. "
                    f"fn: {fn_name}. "
                    f"rpc response: {result}. "
                    f"exception: {e}"
                )
            token_infos.append(token)
        return token_infos

    all_token_infos = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, len(token_name_rpc), batch_size):
            batch = token_name_rpc[i: i + batch_size]
            futures.append(executor.submit(process_batch, batch))

        for future in as_completed(futures):
            try:
                result = future.result()
                all_token_infos.extend(result)
            except Exception as e:
                logger.error(f"Batch processing failed with exception: {e}")

    return all_token_infos


def owner_rpc_requests(web3, make_requests, requests, nft_address, is_batch, abi_list, batch_size, max_workers):
    if len(requests) == 0:
        return []

    fn_name = "ownerOf"
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_token_id_method_data(web3, requests, nft_address, fn_name, abi_list)
    token_name_rpc = list(generate_eth_call_json_rpc(parameters))

    def process_batch(batch):
        if is_batch:
            response = make_requests(params=json.dumps(batch))
        else:
            response = [make_requests(params=json.dumps(batch[0]))]

        token_infos = []
        for data in list(zip_rpc_response(parameters, response)):
            result = rpc_response_to_result(data[1])
            token = data[0]
            value = result[2:] if result is not None else None
            try:
                decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
                token["owner"] = decoded_data[0]

            except Exception as e:
                logger.error(
                    f"Decoding ownerOf failed. "
                    f"token: {token}. "
                    f"fn: {fn_name}. "
                    f"rpc response: {result}. "
                    f"exception: {e}"
                )
            token_infos.append(token)
        return token_infos

    # 分批处理请求
    all_token_infos = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, len(token_name_rpc), batch_size):
            batch = token_name_rpc[i: i + batch_size]
            futures.append(executor.submit(process_batch, batch))

        for future in as_completed(futures):
            try:
                result = future.result()
                all_token_infos.extend(result)
            except Exception as e:
                logger.error(f"Batch processing failed with exception: {e}")

    return all_token_infos


def create_token_status(detail: UniswapV3TokenDetail) -> UniswapV3TokenCurrentStatus:
    return UniswapV3TokenCurrentStatus(
        **{field.name: getattr(detail, field.name) for field in fields(UniswapV3TokenDetail)}
    )


def split_hex_string(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]

    if len(hex_string) == 192:
        part1 = hex_string[:64]
        part2 = hex_string[64:128]
        part3 = hex_string[128:]
        return part1, part2, part3
    else:
        raise ValueError("The data is not belong to Uniswap-V3 Liquidity")
