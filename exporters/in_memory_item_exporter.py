class InMemoryItemExporter:
    def __init__(self, item_types):
        self.item_types = item_types
        self.items = {}

    def open(self):
        for item_type in self.item_types:
            self.items[item_type] = []

    def export_item(self, item):
        item_type = item.get('item', None)
        if item_type is None:
            raise ValueError('type key is not found in item {}'.format(repr(item)))

        self.items[item_type].append(item)

    def close(self):
        pass

    def get_items(self, item_type):
        return self.items[item_type]
