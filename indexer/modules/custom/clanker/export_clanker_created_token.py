import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.clanker.abi.event import token_created_event
from indexer.modules.custom.clanker.domains.tokens import ClankerCreatedTokenD
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportClankerCreatedTokenJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [ClankerCreatedTokenD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[
                            self.user_defined_config["token_factory_address"],
                        ],
                        topics=[token_created_event.get_signature()],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        logs: List[Log] = self._data_buff.get(Log.type(), [])
        for log in logs:
            if log.address.lower() != self.user_defined_config["token_factory_address"].lower():
                continue

            if log.topic0 != token_created_event.get_signature():
                continue

            log_data = token_created_event.decode_log(log)
            self._collect_domain(
                ClankerCreatedTokenD(
                    token_address=log_data["tokenAddress"],
                    lp_nft_id=log_data["lpNftId"],
                    deployer=log_data["deployer"],
                    fid=log_data["fid"],
                    name=log_data["name"],
                    symbol=log_data["symbol"],
                    supply=log_data["supply"],
                    locker_address=log_data["lockerAddress"],
                    cast_hash=log_data["castHash"],
                    block_number=log.block_number,
                )
            )
