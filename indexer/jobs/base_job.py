import logging
import threading
from collections import defaultdict
from datetime import datetime


class BaseJob(object):
    _data_buff = defaultdict(list)
    locks = defaultdict(threading.Lock)

    dependency_types = []
    output_types = []

    @property
    def job_name(self):
        return self.__class__.__name__

    @classmethod
    def discover_jobs(cls):
        return cls.__subclasses__()

    def __init__(self, **kwargs):
        self._entity_types = kwargs['entity_types']
        self._item_exporter = kwargs['item_exporter']
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, **kwargs):
        try:
            self._start()

            start_time = datetime.now()
            self._collect(**kwargs)
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
        pass

    def _end(self):
        pass

    def _collect(self, **kwargs):
        pass

    def _collect_batch(self, iterator):
        pass

    def _collect_item(self, key, data):
        with self.locks[key]:
            self._data_buff[key].append(data)

    def _process(self):
        pass

    def _extract_from_buff(self, keys=None):
        items = []
        for key in keys:
            with self.locks[key]:
                items.extend(self._data_buff[key])

        return items

    def _export(self):
        pass

    def get_buff(self):
        return self._data_buff
