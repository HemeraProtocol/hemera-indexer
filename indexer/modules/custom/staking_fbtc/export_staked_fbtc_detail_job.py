import ast
import configparser
import logging
import os

from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import StakedFBTCDetail
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.STAKED_FBTC_LOGS.value


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [StakedFBTCDetail]
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
            # 获取并解析 STAKED_PROTOCOL_DICT
            staked_protocol_dict_str = config.get(str(chain_id), "STAKED_PROTOCOL_DICT")
            self.staked_protocol_dict = ast.literal_eval(staked_protocol_dict_str)

            # 获取并解析 STAKED_TOPIC0_DICT
            staked_topic0_dict_str = config.get(str(chain_id), "STAKED_TOPIC0_DICT")
            self.staked_topic0_dict = ast.literal_eval(staked_topic0_dict_str)

            # 获取并解析 STAKED_ABI_DICT
            staked_abi_dict_str = config.get(str(chain_id), "STAKED_ABI_DICT")
            self.staked_abi_dict = ast.literal_eval(staked_abi_dict_str)

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Error parsing configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=list(self.staked_abi_dict.keys())),
            ]
        )

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]

        self._batch_work_executor.execute(logs, self._collect_batch, len(logs))
        self._batch_work_executor.wait()

    def _collect_batch(self, logs):
        for log in logs:
            block_number = log.block_number
            block_timestamp = log.block_timestamp
            topic0 = log.topic0
            address = log.address
            if topic0 not in self.staked_abi_dict.keys() or address not in self.staked_protocol_dict.keys():
                continue

            decode_staked = decode_log(self.staked_abi_dict.get(topic0), log)
            staked_entity = StakedFBTCDetail(
                contract_address=address,
                wallet_address=decode_staked["user"],
                amount=decode_staked["amount"],
                protocol_id=self.staked_protocol_dict.get(address, None),
                log_index=log.log_index,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )
            self._collect_item(StakedFBTCDetail.type(), staked_entity)


def _process(self, **kwargs):
    self._data_buff[StakedFBTCDetail.type()].sort(key=lambda x: (x.block_number, x.log_index))
