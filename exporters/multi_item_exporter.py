class MultiItemExporter:
    def __init__(self, item_exporters):
        self.item_exporters = item_exporters

    def open(self):
        for exporter in self.item_exporters:
            exporter.open()

    def export_items(self, items):
        for exporter in self.item_exporters:
            exporter.export_items(items)

    def export_item(self, item):
        for exporter in self.item_exporters:
            exporter.export_item(item)

    def close(self):
        for exporter in self.item_exporters:
            exporter.close()
