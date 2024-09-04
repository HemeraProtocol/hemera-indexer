import configparser
import logging
import os
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.erc20_token_holding.domain.erc20_token_holding import (
    Erc20CurrentTokenHolding,
    Erc20TokenHolding,
)
from indexer.modules.custom.feature_type import FeatureType
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.ERC20_TOKEN_HOLDING.value


class ExportErc20TokenHoldingJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, CurrentTokenBalance]
    output_types = [Erc20TokenHolding, Erc20CurrentTokenHolding]
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
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        if self._need_collected_list is None or len(self._need_collected_list) == 0:
            return
        token_balances = self._data_buff[TokenBalance.type()]
        if token_balances is None or len(token_balances) == 0:
            return
        self._batch_work_executor.execute(
            token_balances,
            self._collect_detail_batch,
            total_items=len(token_balances),
        )

        self._batch_work_executor.wait()
        current_token_balances = self._data_buff[CurrentTokenBalance.type()]
        if current_token_balances is None or len(current_token_balances) == 0:
            return
        self._batch_work_executor.execute(
            current_token_balances,
            self._collect_current_batch,
            total_items=len(current_token_balances),
        )
        self._batch_work_executor.wait()

    def _collect_detail_batch(self, token_balances) -> None:
        if token_balances is None or len(token_balances) == 0:
            return
        for token_balance in token_balances:
            token_address = token_balance.token_address
            if token_address not in self._need_collected_list:
                continue
            self._collect_item(Erc20TokenHolding.type(), parse_balance_to_holding(token_balance))

    def _collect_current_batch(self, current_token_balances) -> None:
        if current_token_balances is None or len(current_token_balances) == 0:
            return
        for current_token_balance in current_token_balances:
            token_address = current_token_balance.token_address
            if token_address not in self._need_collected_list:
                continue
            self._collect_item(Erc20CurrentTokenHolding.type(), parse_current_to_holding(current_token_balance))

    def _process(self, **kwargs):

        self._data_buff[Erc20TokenHolding.type()].sort(key=lambda x: x.block_number)
        self._data_buff[Erc20CurrentTokenHolding.type()].sort(key=lambda x: x.block_number)


def parse_balance_to_holding(token_balance: TokenBalance):
    return Erc20TokenHolding(
        token_address=token_balance.token_address,
        wallet_address=token_balance.address,
        balance=token_balance.balance,
        block_number=token_balance.block_number,
        block_timestamp=token_balance.block_timestamp,
    )


def parse_current_to_holding(token_balance: CurrentTokenBalance):
    return Erc20CurrentTokenHolding(
        token_address=token_balance.token_address,
        wallet_address=token_balance.address,
        balance=token_balance.balance,
        block_number=token_balance.block_number,
        block_timestamp=token_balance.block_timestamp,
    )
