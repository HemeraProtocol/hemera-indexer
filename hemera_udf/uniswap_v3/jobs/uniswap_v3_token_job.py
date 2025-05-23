import logging
from collections import defaultdict

from hemera.common.utils.format_utils import bytes_to_hex_str, to_int_or_none
from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token_transfer import ERC721TokenTransfer
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3PoolFromToken,
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
)
from hemera_udf.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from hemera_udf.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens
from hemera_udf.uniswap_v3.util import AddressManager

logger = logging.getLogger(__name__)


class ExportUniSwapV3TokensJob(FilterTransactionDataJob):
    dependency_types = [Log, ERC721TokenTransfer]
    output_types = [UniswapV3Token, UniswapV3TokenDetail, UniswapV3TokenCurrentStatus, UniswapV3PoolFromToken]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]
        jobs = config.get("jobs", [])
        self._address_manager = AddressManager(jobs)

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self._existing_tokens = self.get_existing_tokens()

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self._address_manager.position_token_address_list),
            ]
        )

    def _process(self, **kwargs):
        self.existing_pools = self.get_existing_pools()
        token_detail_list = []
        call_default_dict = defaultdict()

        burn_tokens_dict = {}
        # 1. when the position_token_address token change
        erc721_token_transfers = [
            tt
            for tt in self._data_buff["erc721_token_transfer"]
            if tt.token_address in self._address_manager.position_token_address_list
        ]
        logs = self._data_buff["log"]

        erc721_token_transfers.sort(key=lambda x: x.block_number)

        for erc721_token_transfer in erc721_token_transfers:
            position_token_address = erc721_token_transfer.token_address
            token_id = erc721_token_transfer.token_id
            block_number = erc721_token_transfer.block_number
            block_timestamp = erc721_token_transfer.block_timestamp
            # transfer to the zero address means the token was burned
            if erc721_token_transfer.to_address == ZERO_ADDRESS:
                # add token detail
                uniswap_v3_token_detail = UniswapV3TokenDetail(
                    position_token_address=position_token_address,
                    pool_address="",
                    token_id=token_id,
                    wallet_address=ZERO_ADDRESS,
                    liquidity=0,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )
                token_detail_list.append(uniswap_v3_token_detail)
                burn_tokens_dict[position_token_address, token_id] = block_number
            #  add the token to the list that need to eth call
            else:
                # if the position was burned, not need to call
                if (position_token_address, token_id) not in burn_tokens_dict:
                    call_dict = {
                        "target": position_token_address,
                        "parameters": [token_id],
                        "block_number": block_number,
                        "user_defined_k": block_timestamp,
                    }
                    call_default_dict[position_token_address, token_id, block_number] = call_dict
        # 2. find out the events that lp change
        for log in logs:
            if log.address in self._address_manager.position_token_address_list:
                position_token_address = log.address
                block_number = log.block_number
                token_id = None
                # different position have different abi
                abi_module = self._address_manager.get_abi_by_position(position_token_address)
                if log.topic0 == abi_module.INCREASE_LIQUIDITY_EVENT.get_signature():
                    decoded_data = abi_module.INCREASE_LIQUIDITY_EVENT.decode_log(log)
                    token_id = decoded_data["tokenId"]
                elif log.topic0 == abi_module.DECREASE_LIQUIDITY_EVENT.get_signature():
                    decoded_data = abi_module.DECREASE_LIQUIDITY_EVENT.decode_log(log)
                    token_id = decoded_data["tokenId"]

                if token_id:
                    call_dict = {
                        "target": position_token_address,
                        "parameters": [token_id],
                        "block_number": block_number,
                        "user_defined_k": log.block_timestamp,
                    }

                    key = (position_token_address, token_id)
                    not_burn_token_flag = key not in burn_tokens_dict
                    before_burn_token_flag = key in burn_tokens_dict and block_number < burn_tokens_dict[key]
                    if not_burn_token_flag or before_burn_token_flag:
                        call_default_dict[position_token_address, token_id, block_number] = call_dict

        # maybe just add this logic only
        keys_to_remove = []

        for key in call_default_dict.keys():
            position_token_address, token_id, block_number = key
            if (position_token_address, token_id) in burn_tokens_dict:
                if block_number >= burn_tokens_dict[position_token_address, token_id]:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            call_default_dict.pop(key)

        # the list that have the call list from #1 and #2
        call_dict_list = list(call_default_dict.values())

        # eth call
        owner_call_list = []
        for call_dict in call_dict_list:
            abi_module = self._address_manager.get_abi_by_position(call_dict.get("target"))

            owner_call_list.append(Call(function_abi=abi_module.OWNER_OF_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(owner_call_list)

        positions_call_list = []
        for call_dict in call_dict_list:
            abi_module = self._address_manager.get_abi_by_position(call_dict.get("target"))
            positions_call_list.append(Call(function_abi=abi_module.POSITIONS_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(positions_call_list)

        positions_data_list = []
        # decode data
        for owner_call, positions_call in zip(owner_call_list, positions_call_list):
            position_token_address = owner_call.target.lower()
            token_id = owner_call.parameters[0]

            block_number = owner_call.block_number
            block_timestamp = owner_call.user_defined_k

            positions = positions_call.returns

            if not owner_call.returns or not positions_call.returns:
                continue

            token0, token1, tick_lower, tick_upper, liquidity, fee, tick_spacing = self.decode_positions_data(
                position_token_address, positions
            )
            data_dict = {
                "owner": owner_call.returns["owner"],
                "position_token_address": position_token_address,
                "token_id": token_id,
                "block_number": block_number,
                "block_timestamp": block_timestamp,
                "token0": token0,
                "token1": token1,
                "tick_lower": tick_lower,
                "tick_upper": tick_upper,
                "liquidity": liquidity,
                "fee": fee,
                "tick_spacing": tick_spacing,
            }
            positions_data_list.append(data_dict)
        self.get_pool_address_by_rpc(positions_data_list)

        for positions_data in positions_data_list:
            # pool_address can be uniquely determined by position_token_address/factory_address, token0, token1, fee
            position_token_address = positions_data.get("position_token_address")
            token_id = positions_data.get("token_id")
            tick_lower = positions_data.get("tick_lower")
            tick_upper = positions_data.get("tick_upper")
            fee = positions_data.get("fee")
            block_number = positions_data.get("block_number")
            block_timestamp = positions_data.get("block_timestamp")
            liquidity = positions_data.get("liquidity")

            pool_address = self.existing_pools.get(
                (
                    position_token_address,
                    positions_data.get("token0"),
                    positions_data.get("token1"),
                    positions_data.get("fee"),
                )
            )
            if not pool_address:
                continue

            if (position_token_address, token_id) not in self._existing_tokens:
                self._existing_tokens.add((position_token_address, token_id))
                token = UniswapV3Token(
                    position_token_address=position_token_address,
                    token_id=token_id,
                    pool_address=pool_address,
                    tick_lower=tick_lower,
                    tick_upper=tick_upper,
                    fee=fee,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )
                self._collect_domain(token)
            # original abi has no owner
            wallet_address = positions_data.get("owner")
            uniswap_v3_token_detail = UniswapV3TokenDetail(
                position_token_address=position_token_address,
                pool_address=pool_address,
                token_id=token_id,
                wallet_address=wallet_address,
                liquidity=liquidity,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )
            token_detail_list.append(uniswap_v3_token_detail)

        token_detail_list.sort(key=lambda t: t.block_number)
        current_token_detail_dict = {}
        for token_detail in token_detail_list:
            uniswap_token_current_status = UniswapV3TokenCurrentStatus(**vars(token_detail))
            current_token_detail_dict[
                uniswap_token_current_status.position_token_address, uniswap_token_current_status.token_id
            ] = uniswap_token_current_status
        self._collect_domains(token_detail_list)
        self._collect_domains(current_token_detail_dict.values())

    def get_pool_address_by_rpc(self, positions_data_list):
        missing_pool_positions_data_dict = {}
        for positions_data in positions_data_list:
            key = (
                positions_data.get("position_token_address"),
                positions_data.get("token0"),
                positions_data.get("token1"),
                # todo: some pools use tick_spacing
                positions_data.get("fee"),
            )
            pool_address = self.existing_pools.get(key)
            if not pool_address:
                missing_pool_positions_data_dict[key] = positions_data

        call_list = []
        for positions_data in missing_pool_positions_data_dict.values():
            position_token_address = positions_data.get("position_token_address")
            factory_address = self._address_manager.get_factory_by_position(position_token_address)
            if not factory_address:
                continue
            abi_module = self._address_manager.get_abi_by_position(position_token_address)

            uniswapv3_type_str = self._address_manager.get_type_str_by_position(position_token_address)
            parameters = [positions_data.get("token0"), positions_data.get("token1")]
            if uniswapv3_type_str in ("uniswapv3", "agni"):
                parameters.append(positions_data.get("fee"))
            elif uniswapv3_type_str == "aerodrome":
                parameters.append(positions_data.get("tick_spacing"))

            call = Call(
                target=factory_address,
                parameters=parameters,
                function_abi=abi_module.GET_POOL_FUNCTION,
                block_number=positions_data.get("block_number"),
                user_defined_k=positions_data.get("block_timestamp"),
            )
            call_list.append(call)
        self.multi_call_helper.execute_calls(call_list)

        for call in call_list:
            returns = call.returns
            if returns:
                pool_address = returns.get("")
                factory_address = call.target.lower()
                position_token_address = self._address_manager.get_position_by_factory(factory_address)

                type_str = self._address_manager.get_type_str_by_position(position_token_address)

                parameters = call.parameters
                token0 = parameters[0]
                token1 = parameters[1]

                tick_spacing = 0
                fee = 0
                if type_str in ("uniswapv3", "agni"):
                    fee = parameters[2]
                elif type_str == "aerodrome":
                    tick_spacing = parameters[3]

                uniswap_v_pool_from_token_positions = UniswapV3PoolFromToken(
                    position_token_address=position_token_address,
                    factory_address=factory_address,
                    pool_address=pool_address,
                    fee=fee,
                    token0_address=token0,
                    token1_address=token1,
                    block_number=call.block_number,
                    block_timestamp=call.user_defined_k,
                    tick_spacing=tick_spacing,
                )
                self._collect_domain(uniswap_v_pool_from_token_positions)
                pool = {
                    (
                        position_token_address,
                        token0,
                        token1,
                        fee,
                    ): pool_address
                }
                self.existing_pools.update(pool)

    def decode_positions_data(self, position_token_address, positions):
        """
        similar abi for now
        """
        # uniswapv3_type_str = self._position_token_address_dict.get(position_token_address)
        token0 = positions.get("token0")
        token1 = positions.get("token1")
        tick_lower = positions.get("tickLower")
        tick_upper = positions.get("tickUpper")
        liquidity = positions.get("liquidity")
        # some position has no fee, could use 0/-1
        fee = positions.get("fee", 0)
        tick_spacing = positions.get("tickSpacing", 0)
        return token0, token1, tick_lower, tick_upper, liquidity, fee, tick_spacing

    def get_existing_tokens(self):
        session = self._service.get_service_session()
        tokens_orm = session.query(
            UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id, UniswapV3Tokens.pool_address
        ).all()
        session.close()

        position_token_address_token_id_pool_address_dict = set()

        for t in tokens_orm:
            position_token_address_token_id_pool_address_dict.add(
                (bytes_to_hex_str(t.position_token_address), t.token_id)
            )

        return position_token_address_token_id_pool_address_dict

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            pools_orm = session.query(UniswapV3Pools).all()
            existing_pools = {
                (
                    bytes_to_hex_str(p.position_token_address),
                    bytes_to_hex_str(p.token0_address),
                    bytes_to_hex_str(p.token1_address),
                    to_int_or_none(p.fee),
                ): bytes_to_hex_str(p.pool_address)
                for p in pools_orm
            }
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
