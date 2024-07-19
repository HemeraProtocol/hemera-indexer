import logging
from datetime import datetime


class BaseJob(object):
    _data_buff = {}

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
        if key not in self._data_buff:
            self._data_buff[key] = []

        self._data_buff[key].append(data)

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
