import logging

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera.indexer.utils.abi_setting import TOKEN_TOTAL_SUPPLY_FUNCTION
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.uniswap_v2.domains import UniswapV2Erc20CurrentTotalSupply, UniswapV2Erc20TotalSupply, UniswapV2Pool
from hemera_udf.uniswap_v2.models.feature_uniswap_v2_pools import UniswapV2Pools

logger = logging.getLogger(__name__)


class ExportUniswapV2TotalSupplyJob(ExtensionJob):
    dependency_types = [ERC20TokenTransfer, UniswapV2Pool]

    output_types = [UniswapV2Erc20TotalSupply, UniswapV2Erc20CurrentTotalSupply]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self._existing_pools = self.get_existing_pools()

    def _process(self, **kwargs):
        uniswap_v2_pools = self._data_buff[UniswapV2Pool.type()]
        for pool in uniswap_v2_pools:
            self._existing_pools.add(pool.pool_address)

        erc_20_token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        uniswapv2_pool_token_transfers = [
            tt for tt in erc_20_token_transfers if tt.token_address in self._existing_pools
        ]

        call_dict = {}
        for token_transfer in uniswapv2_pool_token_transfers:
            token_address = token_transfer.token_address
            block_number = token_transfer.block_number
            call = Call(
                target=token_address,
                function_abi=TOKEN_TOTAL_SUPPLY_FUNCTION,
                block_number=block_number,
                user_defined_k=token_transfer.block_timestamp,
            )
            call_dict[token_address, block_number] = call

        call_list = list(call_dict.values())

        self.multi_call_helper.execute_calls(call_list)

        records = []
        current_dict = {}

        call_list.sort(key=lambda call: call.block_number)

        for call in call_list:
            returns = call.returns
            if returns:
                total_supply = returns.get("totalSupply")

                token_address = call.target.lower()
                erc_total_supply = UniswapV2Erc20TotalSupply(
                    token_address=token_address,
                    total_supply=total_supply,
                    block_number=call.block_number,
                    block_timestamp=call.user_defined_k,
                )

                current_dict[token_address] = UniswapV2Erc20CurrentTotalSupply(**vars(erc_total_supply))
                records.append(erc_total_supply)
        self._collect_domains(records)
        self._collect_domains(current_dict.values())

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            existing_pools = set()

            pools_orm = session.query(UniswapV2Pools).all()
            for pool in pools_orm:
                existing_pools.add(bytes_to_hex_str(pool.pool_address))

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
