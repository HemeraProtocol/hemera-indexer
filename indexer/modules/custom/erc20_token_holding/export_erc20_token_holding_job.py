import configparser
import logging
import os

from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.erc20_token_holding.domain.erc20_token_holding import ExportERC20TokenJobData
from indexer.modules.custom.feature_type import FeatureType
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.ERC20_TOKEN_HOLDING.value


class ExportErc20TokenHoldingJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, CurrentTokenBalance]
    output_types = [ExportERC20TokenJobData]
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
        self._load_config("config.ini", self._chain_id)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self._need_collected_list),
            ]
        )

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            address_list_str = config.get(str(chain_id), "address_list", fallback="")
            self._need_collected_list = [address.strip() for address in address_list_str.split(",") if address.strip()]
            logger.info(f"Need collected list: {self._need_collected_list}")
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")
