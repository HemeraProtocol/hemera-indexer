import logging
from dataclasses import dataclass

from sqlalchemy import text

from indexer.domain import FilterData
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType

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

    def _get_lv_tokens(self):
        session = self._service.get_service_session()

        sql = f"""
            select lv_address from lendle_token_mapping
            union all 
            select variable_debt_Address from lendle_token_mapping
            """
        result = session.execute(text(sql))

        address_list = ['0x' + address[0].hex() for address in result if address[0]]

        return address_list

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    # topics=['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef']
                    addresses=self.address_list
                    # ,addresses=['0xdef3542bb1b2969c1966dd91ebc504f4b37462fe']
                ),
            ]
        )

    def _process(self, **kwargs):
        pass
