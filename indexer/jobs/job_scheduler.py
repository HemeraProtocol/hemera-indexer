import logging
from collections import defaultdict, deque
from typing import List, Set, Type

from common.utils.module_loading import import_submodules
from indexer.jobs.base_job import BaseJob
from indexer.jobs.export_blocks_job import ExportBlocksJob
from indexer.jobs.filter_transaction_data_job import FilterTransactionDataJob

import_submodules('indexer.modules')


# TODO: Import the ExportBlocksJob and ExportTransactionsAndLogsJob classes from the indexer.jobs.export_blocks_job and indexer.jobs.export_transactions_and_logs_job modules

class JobScheduler:
    def __init__(
            self,
            batch_web3_provider,
            batch_web3_debug_provider,
            batch_size=100,
            debug_batch_size=1,
            max_workers=5,
            config=None,
            item_exporters=[],
            required_output_types=[]
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

        self.discover_and_register_job_classes()
        self.required_job_classes = self.get_required_job_classes(required_output_types)
        self.resolved_job_classes = self.resolve_dependencies(self.required_job_classes)

    def get_data_buff(self):
        return BaseJob._data_buff

    def clear_data_buff(self):
        BaseJob._data_buff.clear()

    def discover_and_register_job_classes(self):
        all_subclasses = BaseJob.discover_jobs()
        for cls in all_subclasses:
            self.job_classes.append(cls)
            for output in cls.output_types:
                self.job_map[output.type()].append(cls)
            for dependency in cls.dependency_types:
                self.dependency_map[dependency.type()].append(cls)
            logging.info(
                f"Discovered job class {cls.__name__} with outputs {[output.type() for output in cls.output_types]}")

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
            )
            if isinstance(job, FilterTransactionDataJob):
                filters.append(job.get_filter())

            self.jobs.append(job)

        export_blocks_job = ExportBlocksJob(
            required_output_types=self.required_output_types,
            batch_web3_provider=self.batch_web3_provider,
            batch_web3_debug_provider=self.batch_web3_debug_provider,
            item_exporters=self.item_exporters,
            batch_size=self.batch_size,
            debug_batch_size=self.debug_batch_size,
            max_workers=self.max_workers,
            config=self.config,
            filters=filters
        )
        self.jobs.insert(0, export_blocks_job)

    def run_jobs(self, start_block, end_block):
        if not self.jobs:
            self.instantiate_jobs()
        for job in self.jobs:
            job.run(start_block=start_block, end_block=end_block)
        # TODO: clean data buffer after all jobs are run

    def get_required_job_classes(self, output_types):
        required_job_classes = set()
        job_queue = deque(output_types)
        while job_queue:
            output_type = job_queue.popleft()
            for job_class in self.job_map[output_type.type()]:
                if job_class not in required_job_classes:
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
