import logging
import os

from indexer.exporters.base_exporter import BaseExporter

logger = logging.getLogger(__name__)
from multiprocessing import RLock

lock = RLock()

M_LOCK_TIME: int = int(os.environ.get("M_LOCK_TIME", 20))


class ConsoleItemExporter(BaseExporter):

    def export_items(self, items, **kwargs):
        print(f"Items exported: {len(items)}")
        return
        for item in items:
            self.export_item(item, **kwargs)

    def export_item(self, item, **kwargs):
        if lock.acquire(timeout=M_LOCK_TIME):
            try:
                print(item)
            finally:
                lock.release()
        else:
            logger.error("Lock acquired but not released")

    def batch_finish(self):
        logging.info("Batch finished")
