import logging
from datetime import datetime

from enumeration.entity_type import DEFAULT_COLLECTION, calculate_entity_value


class BaseJob(object):
    _data_buff = {}

    def __init__(self, index_keys=[], entity_types=calculate_entity_value(','.join(DEFAULT_COLLECTION))):
        self._index_keys = index_keys
        self._entity_types = entity_types
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        try:
            self._start()

            start_time = datetime.now()
            self._collect()
            self.logger.info(f"Stage collect finished. Took {datetime.now() - start_time}")

            start_time = datetime.now()
            self._process()
            self.logger.info(f"Stage process finished. Took {datetime.now() - start_time}")

            start_time = datetime.now()
            self._export()
            self.logger.info(f"Stage export finished. Took {datetime.now() - start_time}")

        finally:
            self._end()

    def _start(self):
        for key in self._index_keys:
            self._data_buff[key] = []

    def _end(self):
        pass

    def _collect(self):
        pass

    def _collect_batch(self, iterator):
        pass

    def _collect_item(self, item):
        item_type = item.get('item', None)
        if item_type is None:
            raise ValueError('type key is not found in item {}'.format(repr(item)))

        self._data_buff[item_type].append(item)

    def _process(self):
        pass

    def _extract_from_buff(self, keys=None):
        items = []
        for key in keys:
            if key in self._data_buff:
                items.extend(self._data_buff[key])

        return items

    def _export(self):
        pass

    def get_buff(self):
        return self._data_buff
