import json

from exporters.base_exporter import BaseExporter


class ConsoleItemExporter(BaseExporter):

    def export_items(self, items):
        for item in items:
            self.export_item(item)

    def export_item(self, item):
        print(item)

    def batch_finish(self):
        print("Batch finished")
