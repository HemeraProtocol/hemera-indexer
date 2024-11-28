import logging
from collections import defaultdict

from common.utils.format_utils import bytes_to_hex_str, to_int_or_none
from common.utils.web3_utils import ZERO_ADDRESS
from indexer.domain.log import Log
from indexer.domain.token_transfer import ERC721TokenTransfer
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)

import indexer.modules.custom.uniswap_v3.agni_abi as agni_abi
import indexer.modules.custom.uniswap_v3.swapsicle_abi as swapsicle_abi
import indexer.modules.custom.uniswap_v3.uniswapv3_abi as uniswapv3_abi


class ExportUniSwapV3TokensJob(FilterTransactionDataJob):
    dependency_types = [Log, ERC721TokenTransfer]
    output_types = [UniswapV3Token, UniswapV3TokenDetail, UniswapV3TokenCurrentStatus]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]
        # only index selected position_token_address
        data = config["position_token_address"]
        self._position_token_address_dict = {
            address: uniswapv3_type_str for uniswapv3_type_str, addresses in data.items() for address in addresses
        }

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self._existing_tokens = self.get_existing_tokens()

    def get_filter(self):
        filter_address = list(self._position_token_address_dict.keys())
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=filter_address),
            ]
        )

    def _process(self, **kwargs):
        existing_pools = self.get_existing_pools()
        token_detail_list = []
        call_default_dict = defaultdict()

        burn_tokens_dict = {}
        # 1. when the position_token_address token change
        erc721_token_transfers = [
            tt
            for tt in self._data_buff["erc721_token_transfer"]
            if tt.token_address in self._position_token_address_dict
        ]
        logs = self._data_buff["log"]

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
                call_dict = {
                    "target": position_token_address,
                    "parameters": [token_id],
                    "block_number": block_number,
                    "user_defined_k": block_timestamp,
                }
                call_default_dict[position_token_address, token_id, block_number] = call_dict
        # 2. find out the events that lp change
        for log in logs:
            if log.address in self._position_token_address_dict:
                position_token_address = log.address
                block_number = log.block_number
                token_id = None
                # different position have different abi
                abi_module = self.position_token_address_to_abi_module(position_token_address)
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
                    not_burn_token_flag = (position_token_address, token_id) not in burn_tokens_dict
                    before_burn_token_flag = (
                        position_token_address,
                        token_id,
                    ) in burn_tokens_dict and block_number < burn_tokens_dict[position_token_address, token_id]
                    if not_burn_token_flag or before_burn_token_flag:
                        call_default_dict[position_token_address, token_id, block_number] = call_dict
        # the list that have the call list from #1 and #2
        call_dict_list = list(call_default_dict.values())

        # eth call
        owner_call_list = []
        for call_dict in call_dict_list:
            abi_module = self.position_token_address_to_abi_module(call_dict.get("target"))
            owner_call_list.append(Call(function_abi=abi_module.OWNER_OF_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(owner_call_list)

        positions_call_list = []
        for call_dict in call_dict_list:
            abi_module = self.position_token_address_to_abi_module(call_dict.get("target"))
            positions_call_list.append(Call(function_abi=abi_module.POSITIONS_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(positions_call_list)

        # decode data
        for owner_call, positions_call in zip(owner_call_list, positions_call_list):
            position_token_address = owner_call.target.lower()
            token_id = owner_call.parameters[0]

            block_number = owner_call.block_number
            block_timestamp = owner_call.user_defined_k

            positions = positions_call.returns
            token0, token1, tick_lower, tick_upper, liquidity, fee = self.decode_positions_data(
                position_token_address, positions
            )
            # pool_address can be uniquely determined by position_token_address, token0, token1, fee
            pool_address = existing_pools.get((position_token_address, token0, token1, fee))
            if not pool_address:
                continue

            if (position_token_address, token_id) not in self._existing_tokens:
                self._existing_tokens.append((position_token_address, token_id))
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
            wallet_address = owner_call.returns["owner"]
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

        pass

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
        return token0, token1, tick_lower, tick_upper, liquidity, fee

    def position_token_address_to_abi_module(self, position_token_address):
        uniswapv3_type_str = self._position_token_address_dict.get(position_token_address)
        if uniswapv3_type_str == "swapsicle":
            return swapsicle_abi
        elif uniswapv3_type_str == "uniswapv3":
            return uniswapv3_abi
        elif uniswapv3_type_str == "agni":
            return agni_abi
        else:
            raise NotImplementedError(uniswapv3_type_str)

    def get_existing_tokens(self):
        session = self._service.get_service_session()
        tokens_orm = session.query(
            UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id, UniswapV3Tokens.pool_address
        ).all()
        session.close()

        # position_token_address_token_id_pool_address_dict = {
        #     (bytes_to_hex_str(t.position_token_address), bytes_to_hex_str(t.token_id)): bytes_to_hex_str(t.pool_address)
        #     for t in tokens_orm}

        position_token_address_token_id_pool_address_dict = [
            (bytes_to_hex_str(t.position_token_address), t.token_id) for t in tokens_orm
        ]

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
