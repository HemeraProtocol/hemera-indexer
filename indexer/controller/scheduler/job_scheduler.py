import logging
import os
from collections import defaultdict, deque
from typing import List, Set, Type

from pottery import RedisDict
from redis.client import Redis

from common.models.tokens import Tokens
from common.utils.exception_control import FastShutdownError, HemeraBaseException
from common.utils.format_utils import bytes_to_hex_str
from common.utils.module_loading import import_submodules
from indexer.jobs import CSVSourceJob
from indexer.jobs.base_job import (
    BaseExportJob,
    BaseJob,
    ExtensionJob,
    FilterTransactionDataJob,
    generate_dependency_types,
)
from indexer.jobs.check_block_consensus_job import CheckBlockConsensusJob
from indexer.jobs.export_blocks_job import ExportBlocksJob
from indexer.jobs.source_job.pg_source_job import PGSourceJob

JOB_RETRIES = os.environ.get("JOB_RETRIES", 5)

import_submodules("indexer.modules")


def get_tokens_from_db(service):
    with service.session_scope() as s:
        dict = {}
        result = s.query(Tokens).all()
        if result is not None:
            for token in result:
                dict[bytes_to_hex_str(token.address)] = {
                    "address": bytes_to_hex_str(token.address),
                    "token_type": token.token_type,
                    "name": token.name,
                    "symbol": token.symbol,
                    "decimals": int(token.decimals) if token.decimals is not None else None,
                    "block_number": token.block_number,
                    "total_supply": int(token.total_supply) if token.total_supply is not None else None,
                }
        return dict


def get_source_job_type(source_path: str):
    if source_path.startswith("csvfile://"):
        return CSVSourceJob
    elif source_path.startswith("postgresql://"):
        return PGSourceJob
    else:
        raise ValueError(f"Unknown source job type with source path: {source_path}")


class JobScheduler:
    def __init__(
        self,
        batch_web3_provider,
        batch_web3_debug_provider,
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[],
        required_source_types=[],
        cache="memory",
        multicall=None,
        auto_reorg=True,
        force_filter_mode=False,
    ):
        self.logger = logging.getLogger(__name__)
        self.auto_reorg = auto_reorg
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.batch_size = batch_size
        self._is_multicall = multicall
        self.debug_batch_size = debug_batch_size
        self.max_workers = max_workers
        self.config = config
        required_output_types.sort(key=lambda x: x.type())
        self.required_output_types = required_output_types
        self.required_source_types = required_source_types
        self.load_from_source = config.get("source_path") if "source_path" in config else None
        self.jobs = []
        self.job_classes = []
        self.job_map = defaultdict(list)
        self.dependency_map = defaultdict(list)
        self.pg_service = config.get("db_service") if "db_service" in config else None

        self.discover_and_register_job_classes()
        self.required_job_classes, self.is_pipeline_filter = self.get_required_job_classes(required_output_types)

        if force_filter_mode:
            self.is_pipeline_filter = True

        self.resolved_job_classes = self.resolve_dependencies(self.required_job_classes)
        token_dict_from_db = defaultdict()
        if self.pg_service is not None:
            token_dict_from_db = get_tokens_from_db(self.pg_service)
        if cache is None or cache == "memory":
            BaseJob.init_token_cache(token_dict_from_db)
        else:
            if cache[:5] == "redis":
                try:
                    redis = Redis.from_url(cache)
                    tokens = RedisDict(token_dict_from_db, redis=redis, key="token")
                    BaseJob.init_token_cache(tokens)
                except Exception as e:
                    self.logger.warning(f"Error connecting to redis cache: {e}, using memory cache instead")
                    BaseJob.init_token_cache(token_dict_from_db)
        self.instantiate_jobs()
        self.logger.info("Export output types: ")
        for output_type in self.required_output_types:
            self.logger.info(f"[*] {output_type.type()}")

    def clear_data_buff(self):
        BaseJob._data_buff.clear()

    def get_data_buff(self):
        return BaseJob._data_buff

    def discover_and_register_job_classes(self):
        if self.load_from_source:
            source_job = get_source_job_type(source_path=self.load_from_source)
            if source_job is PGSourceJob:
                source_job.output_types = self.required_source_types
            all_subclasses = [source_job]

            source_output_types = set(source_job.output_types)
            for export_job in BaseExportJob.discover_jobs():
                skip = False
                for output_type in export_job.output_types:
                    if output_type in source_output_types:
                        source_job.output_types = list(set(export_job.output_types + list(source_output_types)))
                        skip = True
                        break
                if not skip:
                    all_subclasses.append(export_job)

        else:
            all_subclasses = BaseExportJob.discover_jobs()

        all_subclasses.extend(ExtensionJob.discover_jobs())
        for cls in all_subclasses:
            generate_dependency_types(cls)
            self.job_classes.append(cls)
            for output in cls.output_types:
                if output.type() in self.job_map:
                    raise Exception(
                        f"Duplicated output type: {output.type()}, job: {cls.__name__}, existing: {self.job_map[output.type()]}, plz check your job definition"
                    )
                self.job_map[output.type()].append(cls)
            for dependency in cls.dependency_types:
                self.dependency_map[dependency.type()].append(cls)

    def get_required_job_classes(self, output_types) -> (List[Type[BaseJob]], bool):
        required_job_classes = set()
        output_type_queue = deque(output_types)
        is_filter = True
        locked_output_types = []

        jobs_set = set()

        for output_type in output_types:
            for job_class in self.job_map[output_type.type()]:
                jobs_set.add(job_class)

        is_locked_flag = False
        for job_class in jobs_set:
            is_filter = job_class.is_filter and is_filter
            if job_class.is_locked and not is_locked_flag:
                is_locked_flag = True
                locked_output_types += job_class.output_types
            elif job_class.is_locked and is_locked_flag:
                raise Exception("Only one job can be locked in a pipeline")
            else:
                pass

        if is_locked_flag and not set(output_types).issubset(set(locked_output_types)):
            raise Exception("Output types must be subset of locked job output types")

        while output_type_queue:
            output_type = output_type_queue.popleft()
            for job_class in self.job_map[output_type.type()]:
                if job_class in self.job_classes:
                    required_job_classes.add(job_class)
                    for dependency in job_class.dependency_types:
                        output_type_queue.append(dependency)
        return required_job_classes, is_filter

    def resolve_dependencies(self, required_jobs: Set[Type[BaseJob]]) -> List[Type[BaseJob]]:
        sorted_order = []
        job_graph = defaultdict(list)
        in_degree = defaultdict(int)

        for job_class in required_jobs:
            for dependency in job_class.dependency_types:
                for parent_class in self.job_map[dependency.type()]:
                    if parent_class in required_jobs:
                        job_graph[parent_class].append(job_class)
                        in_degree[job_class] += 1

        sources = deque([job_class for job_class in required_jobs if in_degree[job_class] == 0])

        while sources:
            job_class = sources.popleft()
            sorted_order.append(job_class)
            for child_class in job_graph[job_class]:
                in_degree[child_class] -= 1
                if in_degree[child_class] == 0:
                    sources.append(child_class)

        if len(sorted_order) != len(required_jobs):
            raise Exception("Dependency cycle detected")

        return sorted_order

    def instantiate_jobs(self):
        filters = []
        for job_class in self.resolved_job_classes:
            if job_class is ExportBlocksJob or job_class is PGSourceJob:
                continue
            job = job_class(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                batch_size=self.batch_size,
                multicall=self._is_multicall,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
            )
            if isinstance(job, FilterTransactionDataJob):
                filters.append(job.get_filter())

            self.jobs.append(job)

        if ExportBlocksJob in self.resolved_job_classes:
            export_blocks_job = ExportBlocksJob(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                batch_size=self.batch_size,
                multicall=self._is_multicall,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                is_filter=self.is_pipeline_filter,
                filters=filters,
            )
            self.jobs.insert(0, export_blocks_job)
        else:
            pg_source_job = PGSourceJob(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                batch_size=self.batch_size,
                multicall=self._is_multicall,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                is_filter=self.is_pipeline_filter,
                filters=filters,
            )
            self.jobs.insert(0, pg_source_job)

    def get_scheduled_jobs(self):
        return self.jobs

    def run_jobs(self, start_block, end_block):
        self.clear_data_buff()

        export_data = {}
        for job in self.jobs:
            job_data = self.job_with_retires(job, start_block=start_block, end_block=end_block)
            export_data.update(job_data)

        for output_type in self.required_output_types:
            message = f"{output_type.type()} : {len(self.get_data_buff().get(output_type.type())) if self.get_data_buff().get(output_type.type()) else 0}"
            self.logger.info(f"{message}")

        return export_data

    def job_with_retires(self, job, start_block, end_block):
        for retry in range(JOB_RETRIES + 1):
            try:
                self.logger.info(f"Task run {job.__class__.__name__}")
                return job.run(start_block=start_block, end_block=end_block)

            except HemeraBaseException as e:
                self.logger.error(
                    f"An rpc response exception occurred while running {job.__class__.__name__}. error: {e}"
                )
                if e.crashable:
                    self.logger.error("Mission will crash immediately.")
                    raise e

                if e.retriable:
                    if retry == JOB_RETRIES:
                        self.logger.info(f"The number of retry is reached limit {JOB_RETRIES}.")
                    else:
                        self.logger.info(f"No: {retry + 1} retry is about to start.")
                else:
                    self.logger.error("Mission will not retry, and exit immediately.")
                    raise e

            except Exception as e:
                self.logger.error(f"An unknown exception occurred while running {job.__class__.__name__}. error: {e}")
                raise e

        self.logger.error(
            f"The job with parameters start_block:{start_block}, end_block:{end_block} "
            f"can't be automatically resumed after reached out limit of retries. Program will exit."
        )
