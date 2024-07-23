import logging
from collections import defaultdict, deque
from typing import List, Set, Type

from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.jobs.export_blocks_job import ExportBlocksJob
from indexer.jobs.export_transactions_and_logs_job import ExportTransactionsAndLogsJob
from indexer.jobs.export_tokens_and_transfers_job import ExportTokensAndTransfersJob
from indexer.jobs.export_traces_job import ExportTracesJob


from indexer.modules.bridge.bedrock.bedrock_bridge_on_l1_job import BedrockBridgeOnL1Job
from indexer.modules.bridge.bedrock.bedrock_bridge_on_l2_job import BedrockBridgeOnL2Job
from indexer.jobs.filter_transaction_data_job import FilterTransactionDataJob
from indexer.modules.bridge.arbitrum.arb_bridge_on_l1_job import ArbitrumBridgeOnL1Job
from indexer.modules.bridge.arbitrum.arb_bridge_on_l2_job import ArbitrumBridgeOnL2Job

def get_all_subclasses(cls: Type) -> Set[Type]:
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses


# TODO: Import the ExportBlocksJob and ExportTransactionsAndLogsJob classes from the indexer.jobs.export_blocks_job and indexer.jobs.export_transactions_and_logs_job modules

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
            item_exporter=ConsoleItemExporter(),
            required_output_types=[]
    ):
        self.entity_types = entity_types
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.item_exporter = item_exporter
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
        all_subclasses = get_all_subclasses(BaseJob)
        for cls in all_subclasses:
            self.job_classes.append(cls)
            for output in cls.output_types:
                self.job_map[output.type()].append(cls)
            for dependency in cls.dependency_types:
                self.dependency_map[dependency.type()].append(cls)
            logging.info(f"Discovered job class {cls.__name__} with outputs {[output.type() for output in cls.output_types]}")

    def instantiate_jobs(self):
        filters = []
        for job_class in self.resolved_job_classes:
            if job_class is ExportBlocksJob:
                continue
            job = job_class(
                entity_types=self.entity_types,
                batch_web3_provider=self.batch_web3_provider,
                batch_web3_debug_provider=self.batch_web3_debug_provider,
                item_exporter=self.item_exporter,
                batch_size=self.batch_size,
                debug_batch_size=self.debug_batch_size,
                max_workers=self.max_workers,
                config=self.config
            )
            if isinstance(job, FilterTransactionDataJob):
                filters.append(job.get_filter())

            self.jobs.append(job)

        export_blocks_job = ExportBlocksJob(
            entity_types=self.entity_types,
            batch_web3_provider=self.batch_web3_provider,
            batch_web3_debug_provider=self.batch_web3_debug_provider,
            item_exporter=self.item_exporter,
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

    def instantiate_job(self, job_class):
        return job_class(
            entity_types=self.entity_types,
            batch_web3_provider=self.batch_web3_provider,
            batch_web3_debug_provider=self.batch_web3_debug_provider,
            item_exporter=self.item_exporter,
            batch_size=self.batch_size,
            debug_batch_size=self.debug_batch_size,
            max_workers=self.max_workers,
            config=self.config
        )
