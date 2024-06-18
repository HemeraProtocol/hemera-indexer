class BaseExporter(object):
    def open(self):
        pass

    def close(self):
        pass

    def export_items(self, items):
        pass

    def export_item(self, item):
        pass

    def batch_finish(self):
        pass
