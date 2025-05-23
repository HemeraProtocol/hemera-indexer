import json
import logging

import hemera_udf.uniswap_v4.abi.uniswapv4_abi as uniswapv4_abi
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.log import Log
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import UniswapV4Hook, UniswapV4Pool
from hemera_udf.uniswap_v4.models.feature_uniswap_v4_pools import UniswapV4Pools
from hemera_udf.uniswap_v4.util import AddressManager

logger = logging.getLogger(__name__)


class ExportUniSwapV4PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV4Pool, UniswapV4Hook]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"]["uniswap_v4_job"]
        self._address_manager = AddressManager(config.get("jobs", []))

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        abi_module.INITIALIZE_EVENT.get_signature()
                        for abi_module in self._address_manager.abi_modules_list
                    ],
                    addresses=self._address_manager.factory_address_list,
                ),
            ]
        )

    def _process(self, **kwargs):
        self.get_pools()

    def get_pools(self):
        processed_count = 0

        for log in self._data_buff[Log.type()]:
            if log.topic0 != uniswapv4_abi.INITIALIZE_EVENT.get_signature():
                continue

            decoded_data = uniswapv4_abi.INITIALIZE_EVENT.decode_log(log)
            pool_id = bytes_to_hex_str(decoded_data["id"])
            if not pool_id:
                logger.warning(f"Pool ID not found for factory {log.address}, tx hash: {log.tx_hash}")
                continue

            position_token_address = self._address_manager.get_position_by_factory(log.address)
            hook_address = decoded_data["hooks"]

            uniswap_v4_pool = UniswapV4Pool(
                factory_address=log.address,
                position_token_address=position_token_address,
                token0_address=decoded_data["currency0"],
                token1_address=decoded_data["currency1"],
                fee=decoded_data["fee"],
                tick_spacing=decoded_data["tickSpacing"],
                pool_address=pool_id,
                hook_address=hook_address,
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
            )
            self._collect_domain(uniswap_v4_pool)
            processed_count += 1

            if hook_address and hook_address != "0x0000000000000000000000000000000000000000":
                hook_type = self.determine_hook_type(hook_address)
                self._collect_domain(
                    UniswapV4Hook(
                        hook_address=hook_address,
                        factory_address=log.address,
                        pool_address=pool_id,
                        hook_type=hook_type,
                        hook_data=json.dumps({"permissions": hook_type}),
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                    )
                )

        logger.info(f"Processed {processed_count} pools")

    def determine_hook_type(self, hook_address):
        # Convert hook address to integer
        addr_int = int(hook_address, 16)
        permissions = []

        permission_flags = {
            13: "before_initialize",
            12: "after_initialize",
            11: "before_add_liquidity",
            10: "after_add_liquidity",
            9: "before_remove_liquidity",
            8: "after_remove_liquidity",
            7: "before_swap",
            6: "after_swap",
            5: "before_donate",
            4: "after_donate",
        }

        for bit, name in permission_flags.items():
            if addr_int & (1 << bit):
                permissions.append(name)

        # Common hook types based on permissions
        if "before_swap" in permissions and "after_swap" in permissions:
            if addr_int & (1 << 3):  # beforeSwapReturnsDelta flag
                return "fee_hook"

        return "unknown"
