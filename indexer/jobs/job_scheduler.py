import logging
from collections import defaultdict, deque
from typing import List, Set

from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob

from indexer.jobs.export_blocks_job import ExportBlocksJob

class JobScheduler:
    def __init__(
            self,
            entity_types,
            batch_web3_provider,
            batch_web3_debug_provider,
            batch_size=100,
            debug_batch_size=1,
            max_workers=5,
            config=None,
            item_exporters=[ConsoleItemExporter()],
    ):
        self.jobs = []
        self.job_map = defaultdict(list)
        self.dependency_map = defaultdict(list)
        self.entity_types = entity_types
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.item_exporters = item_exporters
        self.batch_size = batch_size
        self.debug_batch_size = debug_batch_size
        self.max_workers = max_workers
        self.config = config
        self.discover_and_register_jobs()

    def discover_and_register_jobs(self):
        for cls in BaseJob.__subclasses__():
            job = cls(
                entity_types=self.entity_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                item_exporters=self.item_exporters,
                batch_size=self.batch_size,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config
            )
            self.jobs.append(job)
            for output in job.output_types:
                self.job_map[output.type()].append(job)
            for dependency in job.dependency_types:
                self.dependency_map[dependency.type()].append(job)
            logging.info(f"Registered job {job.job_name} with outputs {[output.type() for output in job.output_types]}")

    def run_jobs(self,
                 start_block,
                 end_block,
                 required_output_types):
        required_output_types = [x.type() for x in required_output_types]
        required_jobs = self.get_required_jobs(required_output_types)
        resolved_order = self.resolve_dependencies(required_jobs)
        for job in resolved_order:
            job.run(start_block=start_block, end_block=end_block)

    def get_required_jobs(self, output_types):
        required_jobs = set()
        job_queue = deque(output_types)
        while job_queue:
            output_type = job_queue.popleft()
            for job in self.job_map[output_type]:
                if job not in required_jobs:
                    required_jobs.add(job)
                    for dependency in job.dependency_types:
                        job_queue.append(dependency.type())
        return required_jobs

    def resolve_dependencies(self, required_jobs: Set[BaseJob]) -> List[BaseJob]:
        sorted_order = []
        job_graph = defaultdict(list)
        in_degree = defaultdict(int)

        for job in required_jobs:
            for dependency in job.dependency_types:
                for parent in self.job_map[dependency.type()]:
                    if parent in required_jobs:
                        job_graph[parent].append(job)
                        in_degree[job] += 1

        sources = deque([job for job in required_jobs if in_degree[job] == 0])

        while sources:
            job = sources.popleft()
            sorted_order.append(job)
            for child in job_graph[job]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    sources.append(child)

        if len(sorted_order) != len(required_jobs):
            raise Exception("Dependency cycle detected")

        return sorted_order
