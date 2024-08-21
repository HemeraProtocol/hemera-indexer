import logging

from indexer.domain.log import Log

from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.staking_fbtc.constants import STAKED_ABI_DICT, STAKED_PROTOCOL_DICT
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import StakedFBTCDetail
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.STAKED_FBTC_LOGS.value


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [StakedFBTCDetail]

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

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=list(STAKED_ABI_DICT.keys())),
            ]
        )

    def _start(self):
        super()._start()

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
            if topic0 not in STAKED_ABI_DICT.keys() or address not in STAKED_PROTOCOL_DICT.keys():
                continue

            decode_staked = decode_log(STAKED_ABI_DICT.get(topic0), log)
            staked_entity = StakedFBTCDetail(
                contract_address=address,
                wallet_address=decode_staked["user"],
                amount=decode_staked["amount"],
                protocol_id=STAKED_PROTOCOL_DICT.get(address, None),
                log_index=log.log_index,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )
            self._collect_item(StakedFBTCDetail.type(), staked_entity)


def _process(self):
    self._data_buff[StakedFBTCDetail.type()].sort(key=lambda x: (x.block_number, x.log_index))
