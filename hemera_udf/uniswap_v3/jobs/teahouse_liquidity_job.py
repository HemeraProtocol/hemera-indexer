import logging

from hemera.indexer.domains.log import Log
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.collection_utils import distinct_collections_by_group
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.uniswap_v3.abi.teahouse_abi import GET_ALL_POSITIONS_FUNCTION
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import TeahouseLiquidityCurrent, TeahouseLiquidityHist

logger = logging.getLogger(__name__)


class TeahouseLiquidityJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [TeahouseLiquidityHist, TeahouseLiquidityCurrent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"]
        self._position_pool_dict = config.get("teahouse_job")
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):
        filter_address_list = list(self._position_pool_dict.keys())

        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=filter_address_list),
            ]
        )

    @staticmethod
    def extract_current_status(records, current_status_domain, keys):
        results = []
        last_records = distinct_collections_by_group(collections=records, group_by=keys, max_key="block_number")
        for last_record in last_records:
            record = current_status_domain(**vars(last_record))
            results.append(record)
        return results

    def _process(self, **kwargs):
        logs = self._data_buff["log"]
        call_dict = {}

        for log in logs:
            if log.address in self._position_pool_dict:
                position_token_address = log.address
                block_number = log.block_number
                call_dict[position_token_address, block_number] = Call(
                    target=position_token_address,
                    function_abi=GET_ALL_POSITIONS_FUNCTION,
                    block_number=block_number,
                    user_defined_k=log.block_timestamp,
                )

        call_list = list(call_dict.values())
        self.multi_call_helper.execute_calls(call_list)

        records = []

        for call in call_list:
            position_token_address = call.target.lower()
            pool_address = self._position_pool_dict[position_token_address]
            block_number = call.block_number
            block_timestamp = call.user_defined_k
            results = call.returns.get("results")
            if results:
                result = results[0]
                liquidity = result.get("liquidity")
                tick_lower = result.get("tickLower")
                tick_upper = result.get("tickUpper")

                record = TeahouseLiquidityHist(
                    position_token_address=position_token_address,
                    pool_address=pool_address,
                    liquidity=liquidity,
                    tick_lower=tick_lower,
                    tick_upper=tick_upper,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )
                records.append(record)

        current_list = self.extract_current_status(
            records, TeahouseLiquidityCurrent, ["position_token_address", "pool_address"]
        )
        self._collect_domains(records)
        self._collect_domains(current_list)
        pass
