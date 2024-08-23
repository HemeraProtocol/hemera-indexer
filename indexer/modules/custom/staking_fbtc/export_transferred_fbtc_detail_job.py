import ast
import configparser
import logging
import os

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import TransferedFBTCDetail
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.TRANSFERRED_FBTC.value


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [TransferedFBTCDetail]
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
        self._load_config("config.ini", self._chain_id)

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._fbtc_address = config.get(str(chain_id), "FBTC_ADDRESS").lower()
            transferred_protocol_dict_str = config.get(str(chain_id), "TRANSFERRED_CONTRACTS_DICT")
            self._transferred_protocol_dict = ast.literal_eval(transferred_protocol_dict_str)

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._fbtc_address]),
            ]
        )

    def _collect(self, **kwargs):
        token_transfers = self._data_buff[ERC20TokenTransfer.type()]

        self._batch_work_executor.execute(token_transfers, self._collect_batch, len(token_transfers))
        self._batch_work_executor.wait()

    def _collect_batch(self, token_transfers):
        for entity in token_transfers:
            token_address = entity.token_address
            if token_address != self._fbtc_address:
                continue
            block_number = entity.block_number
            block_timestamp = entity.block_timestamp
            from_address = entity.from_address
            to_address = entity.to_address
            value = entity.value
            if from_address in self._transferred_protocol_dict.keys():
                contract_address = from_address
                wallet_address = to_address
                balance = -value
                protocol_id = self._transferred_protocol_dict.get(from_address, None)
            elif to_address in self._transferred_protocol_dict.keys():
                contract_address = to_address
                balance = value
                wallet_address = from_address
                protocol_id = self._transferred_protocol_dict.get(to_address, None)
            else:
                continue
            transferred_entity = TransferedFBTCDetail(
                contract_address=contract_address,
                wallet_address=wallet_address,
                amount=balance,
                protocol_id=protocol_id,
                log_index=entity.log_index,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )
            self._collect_item(TransferedFBTCDetail.type(), transferred_entity)


def _process(self, **kwargs):
    self._data_buff[TransferedFBTCDetail.type()].sort(key=lambda x: (x.block_number, x.log_index))
