import logging

from indexer.jobs import FilterTransactionDataJob
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

from hemera.indexer.domains.log import Log
from hemera_udf.thena.abi import BURN_EVENT, LIQUIDITY_FUNCTION, MINT_EVENT
from hemera_udf.thena.domains.feature_thena import ThenaLiquidityDomain

logger = logging.getLogger(__name__)


class ThenaLiquidityJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [ThenaLiquidityDomain]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"]["thena_job"]
        self.thena_liquidity_pool = config.get("thena_liquidity_pool_address")
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[MINT_EVENT.get_signature(), BURN_EVENT.get_signature()],
                    addresses=[self.thena_liquidity_pool],
                ),
            ]
        )

    def _process(self, **kwargs):
        logs = self._data_buff[Log.type()]

        call_dict = {}

        # liquidity
        for log in logs:
            if log.address == self.thena_liquidity_pool and log.topic0 in [
                MINT_EVENT.get_signature(),
                BURN_EVENT.get_signature(),
            ]:
                call_dict[log.block_number] = Call(
                    target=log.address,
                    function_abi=LIQUIDITY_FUNCTION,
                    block_number=log.block_number,
                    user_defined_k=log.block_timestamp,
                )

        call_list = list(call_dict.values())
        self.multi_call_helper.execute_calls(call_list)

        for call in call_list:
            if call.returns:
                pool_address = call.target.lower()
                liquidity = call.returns.get("")
                thena_liquidity_domain = ThenaLiquidityDomain(
                    pool_address=pool_address,
                    block_number=call.block_number,
                    block_timestamp=call.user_defined_k,
                    liquidity=liquidity,
                )
                self._collect_domain(thena_liquidity_domain)
