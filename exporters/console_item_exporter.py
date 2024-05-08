import json


class ConsoleItemExporter:
    def open(self):
        pass

    def export_items(self, items):
        for item in items:
            self.export_item(item)

    def export_item(self, item):
        print(json.dumps(item))

    def close(self):
        pass
