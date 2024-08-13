import logging
import threading
from collections import defaultdict
from datetime import datetime

from web3 import Web3


class BaseJobMeta(type):
    _registry = {}
    _registry_subclass = defaultdict(list)
    logger = logging.getLogger("BaseJobMeta")

    def __new__(mcs, name, bases, attrs):
        new_cls = super().__new__(mcs, name, bases, attrs)

        if name not in ["BaseJob", "BaseSourceJob", "BaseExportJob", "ExtensionJob"] and issubclass(new_cls, BaseJob):
            mcs._registry[name] = new_cls
            mcs._registry_subclass[bases].append(new_cls)

        return new_cls

    @classmethod
    def get_all_subclasses(mcs, bases):
        def get_subclasses(cls):
            subclasses = set()
            for subclass in cls.__subclasses__():
                subclasses.add(subclass)
                subclasses.update(get_subclasses(subclass))
            return subclasses

        return get_subclasses(bases)


class BaseJob(metaclass=BaseJobMeta):
    _data_buff = defaultdict(list)
    locks = defaultdict(threading.Lock)

    tokens = None

    dependency_types = []
    output_types = []

    @classmethod
    def discover_jobs(cls):
        return list(BaseJobMeta.get_all_subclasses(cls))

    @property
    def job_name(self):
        return self.__class__.__name__

    @classmethod
    def init_token_cache(cls, _token=None):
        cls.tokens = _token

    def __init__(self, **kwargs):

        self._required_output_types = kwargs["required_output_types"]
        self._item_exporters = kwargs["item_exporters"]
        self._batch_web3_provider = kwargs["batch_web3_provider"]
        self._web3 = Web3(Web3.HTTPProvider(self._batch_web3_provider.endpoint_uri))
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

    def _collect_domain(self, domain):
        with self.locks[domain.type()]:
            self._data_buff[domain.type()].append(domain)

    def _process(self):
        pass

    def _extract_from_buff(self, keys=None):
        items = []
        for key in keys:
            with self.locks[key]:
                items.extend(self._data_buff[key])

        return items

    def _export(self):
        items = []

        for output_type in self.output_types:
            if output_type in self._required_output_types:
                items.extend(self._extract_from_buff([output_type.type()]))

        for item_exporter in self._item_exporters:
            item_exporter.open()
            item_exporter.export_items(items)
            item_exporter.close()

    def get_buff(self):
        return self._data_buff


class BaseSourceJob(BaseJob):
    pass


class BaseExportJob(BaseJob):
    pass


class ExtensionJob(BaseJob):
    pass
