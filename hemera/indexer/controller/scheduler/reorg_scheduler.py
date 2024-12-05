import logging
from collections import defaultdict, deque
from typing import List, Set, Type

from pottery import RedisDict
from redis.client import Redis

from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.common.utils.module_loading import import_submodules
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.jobs.base_job import BaseExportJob, BaseJob, ExtensionJob
from hemera.indexer.jobs.export_blocks_job import ExportBlocksJob
from hemera.indexer.jobs.export_reorg_job import ExportReorgJob

import_submodules("hemera.indexer.modules")


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


class ReorgScheduler:
    def __init__(
        self,
        batch_web3_provider,
        batch_web3_debug_provider,
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        item_exporters=[],
        required_output_types=[],
        cache="memory",
        multicall=None,
    ):
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.item_exporters = item_exporters
        self.batch_size = batch_size
        self.debug_batch_size = debug_batch_size
        self.max_workers = max_workers
        self.config = config
        self.required_output_types = required_output_types
        self.jobs = []
        self.job_classes = []
        self.job_map = defaultdict(list)
        self.dependency_map = defaultdict(list)
        self.pg_service = config.get("db_service") if "db_service" in config else None
        self._is_multicall = multicall

        self.discover_and_register_job_classes()
        self.required_job_classes = self.get_required_job_classes(required_output_types)
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
                    logging.warning(f"Error connecting to redis cache: {e}, using memory cache instead")
                    BaseJob.init_token_cache(token_dict_from_db)
        self.instantiate_jobs()

    @staticmethod
    def get_data_buff():
        return BaseJob._data_buff

    @staticmethod
    def clear_data_buff():
        BaseJob._data_buff.clear()

    def discover_and_register_job_classes(self):
        all_subclasses = BaseExportJob.discover_jobs()

        all_subclasses.extend(ExtensionJob.discover_jobs())
        for cls in all_subclasses:
            if cls.able_to_reorg:
                self.job_classes.append(cls)
            for output in cls.output_types:
                self.job_map[output.type()].append(cls)
            for dependency in cls.dependency_types:
                self.dependency_map[dependency.type()].append(cls)
            logging.info(
                f"Discovered job class {cls.__name__} with outputs {[output.type() for output in cls.output_types]}"
            )

    def instantiate_jobs(self):
        filters = []
        for job_class in self.resolved_job_classes:
            if job_class is ExportBlocksJob:
                continue
            job = job_class(
                required_output_types=self.required_output_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                item_exporters=self.item_exporters,
                batch_size=self.batch_size,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                reorg=True,
                multicall=self._is_multicall,
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
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config,
                filters=filters,
                reorg=True,
                reorg_jobs=self.job_classes,
                multicall=self._is_multicall,
            )
            self.jobs.insert(0, export_blocks_job)

        export_reorg_job = ExportReorgJob(
            required_output_types=self.required_output_types,
            batch_web3_provider=self.batch_web3_provider,
            batch_web3_debug_provider=self.batch_web3_debug_provider,
            item_exporters=self.item_exporters,
            batch_size=self.batch_size,
            debug_batch_size=self.debug_batch_size,
            max_workers=self.max_workers,
            config=self.config,
            reorg=True,
        )
        self.jobs.append(export_reorg_job)

    def run_jobs(self, start_block, end_block):
        self.clear_data_buff()
        for job in self.jobs:
            job.run(start_block=start_block, end_block=end_block)

    def get_required_job_classes(self, output_types):
        required_job_classes = set()
        job_queue = deque(output_types)
        while job_queue:
            output_type = job_queue.popleft()
            for job_class in self.job_map[output_type.type()]:
                if job_class in self.job_classes:
                    required_job_classes.add(job_class)
                    for dependency in job_class.dependency_types:
                        job_queue.append(dependency)
        return required_job_classes

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
