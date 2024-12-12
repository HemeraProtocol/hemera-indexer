import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.meme_agent.abi.event import *
from indexer.modules.custom.meme_agent.domains.clanker import ClankerCreatedTokenD
from indexer.modules.custom.meme_agent.domains.larry import LarryCreatedTokenD
from indexer.modules.custom.meme_agent.domains.virtuals import VirtualsCreatedTokenD
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportMemeTokenCreatedJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [ClankerCreatedTokenD, LarryCreatedTokenD, VirtualsCreatedTokenD]
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
        self.user_defined_config["larry_factory_address"] = [
            address.lower() for address in self.user_defined_config["larry_factory_address"]
        ]

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[
                            self.user_defined_config["clanker_factory_address_v0"],
                            self.user_defined_config["clanker_factory_address_v1"],
                            self.user_defined_config["virtuals_factory_address"],
                        ]
                        + self.user_defined_config["larry_factory_address"],
                        topics=[
                            clanker_token_created_event_v0.get_signature(),
                            clanker_token_created_event_v1.get_signature(),
                            virtuals_token_created_event.get_signature(),
                            larry_token_created_event.get_signature(),
                        ],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        logs: List[Log] = self._data_buff.get(Log.type(), [])
        for log in logs:
            log_address = log.address.lower()
            if log_address == self.user_defined_config["clanker_factory_address_v0"].lower():
                self._process_clanker_token_created_v0(log)
            elif log_address == self.user_defined_config["clanker_factory_address_v1"].lower():
                self._process_clanker_token_created_v1(log)
            elif log_address == self.user_defined_config["virtuals_factory_address"].lower():
                self._process_virtuals_token_created(log)
            elif log_address in self.user_defined_config["larry_factory_address"]:
                self._process_larry_token_created(log)

    def _process_clanker_token_created_v0(self, log: Log):
        if log.topic0 != clanker_token_created_event_v0.get_signature():
            return

        log_data = clanker_token_created_event_v0.decode_log(log)
        self._collect_domain(
            ClankerCreatedTokenD(
                token_address=log_data["tokenAddress"],
                lp_nft_id=log_data["lpNftId"],
                deployer=log_data["deployer"],
                fid=0,
                name=log_data["name"],
                symbol=log_data["symbol"],
                supply=log_data["supply"],
                locker_address=log_data["lockerAddress"],
                cast_hash="",
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
                version=0,
            )
        )

    def _process_clanker_token_created_v1(self, log: Log):
        if log.topic0 != clanker_token_created_event_v1.get_signature():
            return

        log_data = clanker_token_created_event_v1.decode_log(log)
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
                version=1,
            )
        )

    def _process_virtuals_token_created(self, log: Log):
        if log.topic0 != virtuals_token_created_event.get_signature():
            return

        log_data = virtuals_token_created_event.decode_log(log)
        self._collect_domain(
            VirtualsCreatedTokenD(
                virtual_id=log_data["virtualId"],
                token=log_data["token"],
                dao=log_data["dao"],
                tba=log_data["tba"],
                ve_token=log_data["veToken"],
                lp=log_data["lp"],
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
            )
        )

    def _process_larry_token_created(self, log: Log):
        if log.topic0 != larry_token_created_event.get_signature():
            return

        log_data = larry_token_created_event.decode_log(log)
        self._collect_domain(
            LarryCreatedTokenD(
                token=log_data["token"],
                party=log_data["party"],
                recipient=log_data["recipient"],
                name=log_data["name"],
                symbol=log_data["symbol"],
                eth_value=log_data["ethValue"],
                block_number=log.block_number,
            )
        )
