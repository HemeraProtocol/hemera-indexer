from dataclasses import dataclass

from sqlalchemy import text

from indexer.domain import FilterData
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs


@dataclass
class FilterDomain(FilterData):
    pass


class FilterJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, CurrentTokenBalance, ERC20TokenTransfer]
    output_types = [FilterDomain]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._service = kwargs["config"].get("db_service")
        self.address_list = self._get_lv_tokens()

        # Thetanuts
        # 0xdee7cb1d08ec5e35c4792856f86dd0584db29cfe
        # woofi
        # 0x872b6ff825Da431C941d12630754036278AD7049
        # hourglass
        # 0x326b1129a3ec2ad5c4016d2bb4b912687890ae6c
        # Mitosis
        # 0x6ff000453a9c14f7d3bf381925c8cde565dbce55

        token_list = [
            # Thetanuts
            '0xdee7cb1d08ec5e35c4792856f86dd0584db29cfe',
            # woofi
            '0x872b6ff825da431c941d12630754036278ad7049',
            # hourglass
            '0x326b1129a3ec2ad5c4016d2bb4b912687890ae6c',
            # Mitosis
            '0x6ff000453a9c14f7d3bf381925c8cde565dbce55',
            # circuit
            '0x59e641de941cc794cdf6152eda0ef51210373d95',
        ]
        self.address_list.extend(token_list)

        # self.address_list = ['0x59e641de941cc794cdf6152eda0ef51210373d95']


    def _get_lv_tokens(self):
        session = self._service.get_service_session()

        sql = f"""
            select lv_address from lendle_token_mapping
            union distinct 
            select variable_debt_Address from lendle_token_mapping
            union distinct 
             select lv_address from aurelius_token_mapping
            union distinct 
            select variable_debt_Address from aurelius_token_mapping
            """
        result = session.execute(text(sql))

        address_list = ['0x' + address[0].hex() for address in result if address[0]]

        return address_list

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=self.address_list
                ),
            ]
        )

    def _process(self, **kwargs):
        pass
