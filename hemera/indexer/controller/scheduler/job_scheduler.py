import io
import logging
import os
from collections import defaultdict, deque
from distutils.util import strtobool
from typing import List, Set, Type, Union

import pandas as pd
from pottery import RedisDict
from redis.client import Redis
from tqdm import tqdm

from hemera.common.utils.exception_control import HemeraBaseException
from hemera.common.utils.module_loading import import_submodules
from hemera.indexer.jobs import CSVSourceJob
from hemera.indexer.jobs.base_job import (
    BaseExportJob,
    BaseJob,
    ExtensionJob,
    FilterTransactionDataJob,
    generate_dependency_types,
)
from hemera.indexer.jobs.export_blocks_job import ExportBlocksJob
from hemera.indexer.jobs.source_job.pg_source_job import PGSourceJob
from hemera.indexer.utils.buffer_service import BufferService

JOB_RETRIES = int(os.environ.get("JOB_RETRIES", "5"))
PGSOURCE_ACCURACY = bool(strtobool(os.environ.get("PGSOURCE_ACCURACY", "false")))


def get_tokens_from_db(service):
    with service.cursor_scope() as cur:
        csv_data = io.StringIO()
        copy_query = "COPY tokens TO STDOUT WITH CSV HEADER"
        cur.copy_expert(copy_query, csv_data)
        csv_data.seek(0)

        dtype = {
            "address": str,
            "token_type": str,
            "name": str,
            "symbol": str,
            "decimals": str,
            "total_supply": str,
            "fail_balance_of_count": int,
            "fail_total_supply_count": int,
            "block_number": int,
        }
        converters = {
            "no_balance_of": lambda x: str(x).lower() in ["t", "true", "1"],
            "no_total_supply": lambda x: str(x).lower() in ["t", "true", "1"],
        }
        df = pd.read_csv(csv_data, dtype=dtype, converters=converters)
        df["address"] = df["address"].str.replace(r"\\x", "0x", regex=True)

        token_dict = {}
        for row in tqdm(df.itertuples(), total=len(df), desc="Loading tokens"):
            address = row.address
            token_dict[address] = {
                "address": address,
                "token_type": row.token_type,
                "name": row.name,
                "symbol": row.symbol,
                "decimals": int(row.decimals) if pd.notna(row.decimals) else None,
                "total_supply": int(row.total_supply) if pd.notna(row.total_supply) else None,
                "no_total_supply": row.no_total_supply,
                "fail_total_supply_count": row.fail_total_supply_count,
                "no_balance_of": row.no_balance_of,
                "fail_balance_of_count": row.fail_balance_of_count,
                "block_number": row.block_number,
            }
        return token_dict


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
        buffer_service: Union[dict, BufferService] = defaultdict(list),
        required_output_types=[],
        required_source_types=[],
        cache="memory",
        multicall=None,
        auto_reorg=True,
        force_filter_mode=False,
    ):
        import_submodules("hemera_udf")
        self.logger = logging.getLogger(__name__)
        self.auto_reorg = auto_reorg
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.buffer_service = buffer_service
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
        discovered_job_classes = BaseExportJob.discover_jobs()
        discovered_job_classes.extend(ExtensionJob.discover_jobs())

        for job in discovered_job_classes:
            generate_dependency_types(job)

        if self.load_from_source:
            source_job = get_source_job_type(source_path=self.load_from_source)
            if source_job is PGSourceJob:
                source_job.output_types = self.required_source_types
            all_subclasses = [source_job]

            source_output_types = set(source_job.output_types)
            for job in discovered_job_classes:
                skip = False
                for output_type in job.output_types:
                    if output_type in source_output_types:
                        if not PGSOURCE_ACCURACY:
                            source_job.output_types = list(set(job.output_types + list(source_output_types)))
                        skip = True
                        break
                if not skip:
                    all_subclasses.append(job)

        else:
            all_subclasses = discovered_job_classes

        for cls in all_subclasses:
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

        if len(required_job_classes) == 0:
            raise Exception(
                "No job classes were required. The following are possible reasons: "
                "1. The udf job is not recognized by indexer. "
                "2. The input dependency and output dataclass are not correctly bound to the udf job. "
                "3. DynamicEntityTypeRegistry failed to register correctly."
            )

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
        BaseJob._data_buff = self.buffer_service

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

        if PGSourceJob in self.resolved_job_classes:
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

        for job in self.jobs:
            self.job_with_retires(job, start_block=start_block, end_block=end_block)

        for output_type in self.required_output_types:
            message = f"{output_type.type()} : {len(self.get_data_buff().get(output_type.type())) if self.get_data_buff().get(output_type.type()) else 0}"
            self.logger.info(f"{message}")

    def job_with_retires(self, job, start_block, end_block):
        for retry in range(JOB_RETRIES + 1):
            try:
                self.logger.info(f"Task run {job.__class__.__name__}")
                job.run(start_block=start_block, end_block=end_block)
                return

            except HemeraBaseException as e:
                self.logger.error(f"An expected exception occurred while running {job.__class__.__name__}. error: {e}")
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
