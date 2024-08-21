import logging
from multiprocessing import Process

from enumeration.entity_type import ALL_ENTITY_COLLECTIONS, calculate_entity_value, generate_output_types
from enumeration.schedule_mode import ScheduleMode
from indexer.controller.reorg_controller import ReorgController
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.block import Block
from indexer.exporters.postgres_item_exporter import PostgresItemExporter
from indexer.jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class CheckBlockConsensusJob(BaseJob):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_batch_end_block = None
        config = kwargs["config"]
        self.check_switch = config.get("db_service", None) is not None

        if self.check_switch:
            entity_types = calculate_entity_value(",".join(ALL_ENTITY_COLLECTIONS))
            output_types = list(generate_output_types(entity_types))
            reorg_job_scheduler = JobScheduler(
                batch_web3_provider=self._batch_web3_provider,
                batch_web3_debug_provider=kwargs["batch_web3_debug_provider"],
                item_exporters=PostgresItemExporter(config["db_service"]),
                batch_size=kwargs["batch_size"],
                debug_batch_size=kwargs["debug_batch_size"],
                required_output_types=output_types,
                schedule_mode=ScheduleMode.REORG,
                config=config,
            )

            self.reorg_controller = ReorgController(
                batch_web3_provider=kwargs["batch_web3_provider"],
                job_scheduler=reorg_job_scheduler,
                ranges=1000,
                config=config,
            )

    def _process(self, **kwargs):
        if not self.check_switch:
            return

        batch_blocks = self._data_buff[Block.type()]

        if self.last_batch_end_block is not None:
            batch_blocks = [self.last_batch_end_block] + batch_blocks

        batch_blocks.reverse()
        parent_hash = batch_blocks[0]["parent_hash"]
        for block in batch_blocks[1:]:
            block_hash = block["hash"]
            if block_hash != parent_hash:
                # non-consensus detected
                fixing_thread = Process(target=self.reorg_controller.action, kwargs={"block_number": block["number"]})
                fixing_thread.start()
                break

            parent_hash = block["parent_hash"]

        self.last_batch_end_block = batch_blocks[-1]
