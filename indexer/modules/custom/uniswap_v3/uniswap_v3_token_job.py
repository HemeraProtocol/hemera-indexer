import logging
from collections import defaultdict

from common.utils.web3_utils import ZERO_ADDRESS

from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools

from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens

from indexer.domain.log import Log
from indexer.domain.token_transfer import ERC721TokenTransfer
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail, UniswapV3Pool,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from common.utils.format_utils import bytes_to_hex_str, to_float_or_none, to_int_or_none

logger = logging.getLogger(__name__)

from indexer.modules.custom.uniswap_v3.swapsicle_abi import (
    DECREASE_LIQUIDITY_EVENT,
    INCREASE_LIQUIDITY_EVENT,
    OWNER_OF_FUNCTION,
    POSITIONS_FUNCTION
)


class ExportUniSwapV3TokensJob(FilterTransactionDataJob):
    dependency_types = [Log, ERC721TokenTransfer]
    output_types = [UniswapV3Token, UniswapV3TokenDetail, UniswapV3TokenCurrentStatus]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]
        self._position_token_address_list = config['position_token_address']

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self._existing_tokens = self.get_existing_tokens()

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self._position_token_address_list),
            ]
        )

    def _process(self, **kwargs):
        existing_pools = self.get_existing_pools()
        token_detail_list = []
        call_default_dict = defaultdict()

        burn_tokens_dict = {}

        erc721_token_transfers = [tt for tt in self._data_buff['erc721_token_transfer'] if
                                  tt.token_address in self._position_token_address_list]
        logs = self._data_buff['log']

        for erc721_token_transfer in erc721_token_transfers:
            position_token_address = erc721_token_transfer.token_address
            token_id = erc721_token_transfer.token_id
            block_number = erc721_token_transfer.block_number
            block_timestamp = erc721_token_transfer.block_timestamp

            if erc721_token_transfer.to_address == ZERO_ADDRESS:
                # add token detail
                uniswap_v3_token_detail = UniswapV3TokenDetail(position_token_address=position_token_address,
                                                               pool_address='',
                                                               token_id=token_id, wallet_address=ZERO_ADDRESS,
                                                               liquidity=0,
                                                               block_number=block_number,
                                                               block_timestamp=block_timestamp)
                token_detail_list.append(uniswap_v3_token_detail)
                burn_tokens_dict[position_token_address, token_id] = block_number


            else:
                call_dict = {
                    'target': position_token_address,
                    'parameters': [token_id],
                    'block_number': block_number,
                    'user_defined_k': block_timestamp
                }
                call_default_dict[position_token_address, token_id, block_number] = call_dict

        for log in logs:
            if log.address in self._position_token_address_list:
                position_token_address = log.address
                block_number = log.block_number
                token_id = None

                if log.topic0 == INCREASE_LIQUIDITY_EVENT.get_signature():
                    decoded_data = INCREASE_LIQUIDITY_EVENT.decode_log(log)
                    token_id = decoded_data['tokenId']
                elif log.topic0 == DECREASE_LIQUIDITY_EVENT.get_signature():
                    decoded_data = DECREASE_LIQUIDITY_EVENT.decode_log(log)
                    token_id = decoded_data['tokenId']

                if token_id:
                    call_dict = {
                        'target': position_token_address,
                        'parameters': [token_id],
                        'block_number': block_number,
                        'user_defined_k': log.block_timestamp
                    }
                    not_burn_token_flag = (position_token_address, token_id) not in burn_tokens_dict
                    before_burn_token_flag = (position_token_address, token_id) in burn_tokens_dict and block_number < \
                                             burn_tokens_dict[position_token_address, token_id]
                    if not_burn_token_flag or before_burn_token_flag:
                        call_default_dict[position_token_address, token_id, block_number] = call_dict

        call_dict_list = list(call_default_dict.values())
        # # get pool for no pools token id
        # missing_pool_address_in_existing_tokens = []
        # position_token_address_list = {k[:2] for k in call_default_dict.keys()}
        # for position_token_address, token_id in position_token_address_list:
        #     token_id_key = (position_token_address, token_id)
        #     if token_id_key not in self._existing_tokens and token_id_key not in missing_pool_address_in_existing_tokens:
        #         missing_pool_address_in_existing_tokens.append(token_id_key)

        # pool_address_call_list = []

        owner_call_list = []
        for call_dict in call_dict_list:
            owner_call_list.append(Call(function_abi=OWNER_OF_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(owner_call_list)

        positions_call_list = []
        for call_dict in call_dict_list:
            positions_call_list.append(Call(function_abi=POSITIONS_FUNCTION, **call_dict))
        self.multi_call_helper.execute_calls(positions_call_list)

        for owner_call, positions_call in zip(owner_call_list, positions_call_list):
            position_token_address = owner_call.target.lower()
            token_id = owner_call.parameters[0]

            block_number = owner_call.block_number
            block_timestamp = owner_call.user_defined_k

            positions = positions_call.returns
            token0 = positions.get('token0')
            token1 = positions.get('token1')
            tick_lower = positions.get('tickLower')
            tick_upper = positions.get('tickUpper')
            liquidity = positions.get('liquidity')
            fee = positions.get('fee', 0)
            pool_address = existing_pools.get((position_token_address, token0, token1, fee))
            if not pool_address:
                continue

            if (position_token_address, token_id) not in self._existing_tokens:
                self._existing_tokens.append((position_token_address, token_id))
                token = UniswapV3Token(position_token_address=position_token_address, token_id=token_id,
                                       pool_address=pool_address, tick_lower=tick_lower, tick_upper=tick_upper, fee=fee,
                                       block_number=block_number, block_timestamp=block_timestamp)
                self._collect_domain(token)

            wallet_address = owner_call.returns['owner']
            uniswap_v3_token_detail = UniswapV3TokenDetail(position_token_address=position_token_address,
                                                           pool_address=pool_address,
                                                           token_id=token_id, wallet_address=wallet_address,
                                                           liquidity=liquidity,
                                                           block_number=block_number, block_timestamp=block_timestamp)
            token_detail_list.append(uniswap_v3_token_detail)

        token_detail_list.sort(key=lambda t: t.block_number)
        current_token_detail_dict = {}
        for token_detail in token_detail_list:
            uniswap_token_current_status = UniswapV3TokenCurrentStatus(**vars(token_detail))
            current_token_detail_dict[
                uniswap_token_current_status.position_token_address, uniswap_token_current_status.token_id] = uniswap_token_current_status
        self._collect_domains(token_detail_list)
        self._collect_domains(current_token_detail_dict.values())

        pass

    def get_existing_tokens(self):
        session = self._service.get_service_session()
        tokens_orm = (
            session.query(UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id,
                          UniswapV3Tokens.pool_address)
            .all()
        )
        session.close()

        # position_token_address_token_id_pool_address_dict = {
        #     (bytes_to_hex_str(t.position_token_address), bytes_to_hex_str(t.token_id)): bytes_to_hex_str(t.pool_address)
        #     for t in tokens_orm}

        position_token_address_token_id_pool_address_dict = [
            (bytes_to_hex_str(t.position_token_address), t.token_id)
            for t in tokens_orm]

        return position_token_address_token_id_pool_address_dict

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            pools_orm = (
                session.query(UniswapV3Pools)
                .all()
            )
            existing_pools = {
                (bytes_to_hex_str(p.position_token_address),
                 bytes_to_hex_str(p.token0_address),
                 bytes_to_hex_str(p.token1_address),
                 to_int_or_none(p.fee)): bytes_to_hex_str(p.pool_address)
                for p in pools_orm
            }
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
