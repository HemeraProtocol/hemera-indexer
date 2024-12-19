import logging

from hemera.indexer.exporters.base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class ConsoleItemExporter(BaseExporter):

    def export_items(self, items, **kwargs):
        for item in items:
            self.export_item(item, **kwargs)

    def export_item(self, item, **kwargs):
        print(item)

    def batch_finish(self):
        logging.info("Batch finished")
