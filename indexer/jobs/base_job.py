import logging
import threading
from collections import defaultdict
from datetime import datetime

from web3 import Web3

from common.converter.pg_converter import domain_model_mapping
from common.services.postgresql_service import PostgreSQLService
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import to_snake_case
from indexer.domain import Domain
from indexer.domain.transaction import Transaction
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.reorg import should_reorg
from indexer.utils.thread_local_proxy import ThreadLocalProxy


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
    _data_buff_lock = defaultdict(threading.Lock)

    tokens = None

    is_locked = False
    is_filter = False
    dependency_types = []
    output_types = []
    able_to_reorg = False
    able_to_multi_process = False

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

        self._multiprocess = kwargs.get("multiprocess", False)
        self._required_output_types = kwargs["required_output_types"]
        self._web3_provider_uri = kwargs["web3_provider_uri"]
        self._web3_debug_provider_uri = kwargs["web3_debug_provider_uri"]
        # self._batch_web3_provider = kwargs["batch_web3_provider"]
        self._batch_size = kwargs["batch_size"]
        self._max_workers = kwargs["max_workers"]
        self._is_batch = kwargs["batch_size"] > 1 if kwargs.get("batch_size") else False
        self._reorg = kwargs["reorg"] if kwargs.get("reorg") else False

        self._chain_id = kwargs.get("chain_id", None)

        self._should_reorg = False
        self._should_reorg_type = set()
        self._service_url = kwargs["config"].get("db_service", None)

        job_name_snake = to_snake_case(self.job_name)
        self.user_defined_config = kwargs["config"][job_name_snake] if kwargs["config"].get(job_name_snake) else {}

        if not self.able_to_multi_process and self._multiprocess:
            raise FastShutdownError(
                f"Job: {self.__class__.__name__} can not run in multiprocessing mode, "
                f"please check runtime parameter or modify job code."
            )

        if not self._multiprocess:
            self.logger_name = self.__class__.__name__
            self.logger = logging.getLogger(self.logger_name)
            self._batch_web3_provider = ThreadLocalProxy(
                lambda: get_provider_from_uri(self._web3_provider_uri, batch=True)
            )
            self._web3 = Web3(Web3.HTTPProvider(self._web3_provider_uri))
            self._chain_id = (
                (self._web3.eth.chain_id if self._batch_web3_provider else None)
                if self._chain_id is None
                else self._chain_id
            )

    def run(self, **kwargs):
        try:
            self._start(**kwargs)

            if self.able_to_reorg and self._reorg:
                start_time = datetime.now()
                self.logger.info(f"Stage _pre_reorg starting.")
                self._pre_reorg(**kwargs)
                self.logger.info(f"Stage _pre_reorg finished. Took {datetime.now() - start_time}")

            if not self._reorg or self._should_reorg:
                self._collect(**kwargs)
                self._process(**kwargs)

        finally:
            self._end()

        return {dataclass.type(): self._data_buff[dataclass.type()] for dataclass in self.output_types}

    def _start(self, **kwargs):
        if self._multiprocess:
            self.logger_name = f"{self.__class__.__name__}-{kwargs['processor']}"
            self.logger = logging.getLogger(self.logger_name)
            self._batch_web3_provider = ThreadLocalProxy(
                lambda: get_provider_from_uri(self._web3_provider_uri, batch=True)
            )
            self._web3 = Web3(Web3.HTTPProvider(self._web3_provider_uri))
            self._chain_id = (
                (self._web3.eth.chain_id if self._batch_web3_provider else None)
                if self._chain_id is None
                else self._chain_id
            )

        for dataclass in self.output_types:
            self._data_buff[dataclass.type()].clear()

    def _pre_reorg(self, **kwargs):
        if self._service_url is None:
            raise FastShutdownError("PG Service is not set")

        service = PostgreSQLService(self._service_url)
        reorg_block = int(kwargs["start_block"])

        output_table = {}
        for domain in self.output_types:
            output_table[domain_model_mapping[domain]["table"]] = domain.type()
            # output_table.add(domain_model_mapping[domain.__name__]["table"])

        for table in output_table.keys():
            if should_reorg(reorg_block, table, service):
                self._should_reorg_type.add(output_table[table])
                self._should_reorg = True

    def _end(self):
        if self._reorg:
            for output in self.output_types:
                if output.type() not in self._should_reorg_type and output.type() in self._data_buff.keys():
                    self._data_buff.pop(output.type())

    def _collect(self, **kwargs):
        pass

    def _collect_batch(self, iterator):
        pass

    def _collect_item(self, key, data):
        with self._data_buff_lock[key]:
            self._data_buff[key].append(data)

    def _collect_items(self, key, data_list):
        with self._data_buff_lock[key]:
            self._data_buff[key].extend(data_list)

    def _collect_domain(self, domain):
        with self._data_buff_lock[domain.type()]:
            self._data_buff[domain.type()].append(domain)

    def _collect_domains(self, domains):
        for domain in domains:
            self._collect_domain(domain)

    def _get_domain(self, domain):
        return self._data_buff[domain.type()] if domain.type() in self._data_buff else []

    def _get_domains(self, domains: list[Domain]):
        res = []
        for domain in domains:
            res += self._data_buff[domain.type()]
        return res

    def _process(self, **kwargs):
        pass

    def _extract_from_buff(self, keys=None):
        items = []
        for key in keys:
            with self._data_buff_lock[key]:
                items.extend(self._data_buff[key])

        return items

    def get_buff(self):
        return self._data_buff


class BaseSourceJob(BaseJob):
    pass


class BaseExportJob(BaseJob):
    pass


class ExtensionJob(BaseJob):
    pass


class FilterTransactionDataJob(ExtensionJob):
    dependency_types = [Transaction]
    output_types = []
    is_filter = True

    def get_filter(self):
        raise NotImplementedError

    def get_filter_transactions(self):
        return list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
