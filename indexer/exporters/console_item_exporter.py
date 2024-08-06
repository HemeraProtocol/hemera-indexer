import logging

from indexer.exporters.base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class ConsoleItemExporter(BaseExporter):

    def export_items(self, items):
        for item in items:
            self.export_item(item)

    def export_item(self, item):
        print(item)

    def batch_finish(self):
        logging.info("Batch finished")
