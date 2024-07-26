import collections
from typing import List

from indexer.domain import Domain


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


def group_by_item_type(items: List[Domain]):
    result = collections.defaultdict(list)
    for item in items:
        key = item.__class__
        result[key].append(item)

    return result
