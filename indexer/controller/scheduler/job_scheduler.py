import logging
from collections import defaultdict, deque
from typing import List, Set, Type

from pottery import RedisDict
from redis.client import Redis

from common.models.tokens import Tokens
from common.services.postgresql_service import session_scope
from common.utils.module_loading import import_submodules
from enumeration.record_level import RecordLevel
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs import CSVSourceJob
from indexer.jobs.base_job import BaseExportJob, BaseJob, ExtensionJob, FilterTransactionDataJob
from indexer.jobs.check_block_consensus_job import CheckBlockConsensusJob
from indexer.jobs.export_blocks_job import ExportBlocksJob
from indexer.jobs.source_job.pg_source_job import PGSourceJob
from indexer.utils.abi import bytes_to_hex_str
from indexer.utils.exception_recorder import ExceptionRecorder

import_submodules("indexer.modules")
exception_recorder = ExceptionRecorder()


def get_tokens_from_db(session):
    with session_scope(session) as s:
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
        item_exporters=[ConsoleItemExporter()],
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
        self.item_exporters = item_exporters
        self.batch_size = batch_size
        self._is_multicall = multicall
        self.debug_batch_size = debug_batch_size
        self.max_workers = max_workers
        self.config = config
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
            token_dict_from_db = get_tokens_from_db(self.pg_service.get_service_session())
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
        self.logger.info("Export output types: %s", required_output_types)

    def get_required_job_classes(self, output_types) -> (List[Type[BaseJob]], bool):
        required_job_classes = set()
        output_type_queue = deque(output_types)
        is_filter = True
        for output_type in output_types:
            for job_class in self.job_map[output_type.type()]:
                is_filter = job_class.is_filter and is_filter

        while output_type_queue:
            output_type = output_type_queue.popleft()
            for job_class in self.job_map[output_type.type()]:
                if job_class in self.job_classes:
                    required_job_classes.add(job_class)
                    for dependency in job_class.dependency_types:
                        output_type_queue.append(dependency)
        return required_job_classes, is_filter

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
            self.job_classes.append(cls)
            for output in cls.output_types:
                self.job_map[output.type()].append(cls)
            for dependency in cls.dependency_types:
                self.dependency_map[dependency.type()].append(cls)
            self.logger.info(
                f"Discovered job class {cls.__name__} with outputs {[output.type() for output in cls.output_types]}"
            )

    def instantiate_jobs(self):
        filters = []
        for job_class in self.resolved_job_classes:
            if job_class is ExportBlocksJob or job_class is PGSourceJob:
                continue
            job = job_class(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                item_exporters=self.item_exporters,
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
                item_exporters=self.item_exporters,
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
                item_exporters=self.item_exporters,
                batch_size=self.batch_size,
                multicall=self._is_multicall,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                is_filter=self.is_pipeline_filter,
                filters=filters,
            )
            self.jobs.insert(0, pg_source_job)

        if self.auto_reorg:
            check_job = CheckBlockConsensusJob(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                item_exporters=self.item_exporters,
                batch_size=self.batch_size,
                multicall=self._is_multicall,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                filters=filters,
            )
            self.jobs.append(check_job)

    def run_jobs(self, start_block, end_block):
        self.clear_data_buff()
        try:
            for job in self.jobs:
                job.run(start_block=start_block, end_block=end_block)

            for key, value in self.get_data_buff().items():
                message = f"{key}: {len(value)}"
                self.logger.info(message)
                exception_recorder.log(
                    block_number=-1, dataclass=key, message_type="item_counter", message=message, level=RecordLevel.INFO
                )
        except Exception as e:
            raise e
        finally:
            exception_recorder.force_to_flush()

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
