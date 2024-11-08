import logging
import threading
from collections import defaultdict
from datetime import datetime
from typing import List, Type, get_args, get_origin, get_type_hints

from deprecated import deprecated
from web3 import Web3

from common.converter.pg_converter import domain_model_mapping
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import to_snake_case
from indexer.domain import Domain
from indexer.domain.transaction import Transaction
from indexer.utils.reorg import should_reorg


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

    is_locked = False
    is_filter = False
    dependency_types = []
    output_types = []
    able_to_reorg = False

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
        self._is_batch = kwargs["batch_size"] > 1 if kwargs.get("batch_size") else False
        self._reorg = kwargs["reorg"] if kwargs.get("reorg") else False

        self._chain_id = kwargs.get("chain_id") or (self._web3.eth.chain_id if self._batch_web3_provider else None)

        self._should_reorg = False
        self._should_reorg_type = set()
        self._service = kwargs["config"].get("db_service", None)

        job_name_snake = to_snake_case(self.job_name)
        self.user_defined_config = kwargs["config"][job_name_snake] if kwargs["config"].get(job_name_snake) else {}

    def run(self, **kwargs):
        try:
            self._start(**kwargs)

            if self.able_to_reorg and self._reorg:
                start_time = datetime.now()
                self.logger.info(f"Stage _pre_reorg starting.")
                self._pre_reorg(**kwargs)
                self.logger.info(f"Stage _pre_reorg finished. Took {datetime.now() - start_time}")

            if not self._reorg or self._should_reorg:
                if is_overwrite_process_function(self.__class__):
                    parameters = self._build_process_function_parameter()
                    self._process_function(**parameters)
                else:
                    self._collect(**kwargs)
                    self._process(**kwargs)

            if not self._reorg:
                self._export()

        finally:
            self._end()

    def _start(self, **kwargs):
        pass

    def _pre_reorg(self, **kwargs):
        if self._service is None:
            raise FastShutdownError("PG Service is not set")

        reorg_block = int(kwargs["start_block"])

        output_table = {}
        for domain in self.output_types:
            output_table[domain_model_mapping[domain.__name__]["table"]] = domain.type()
            # output_table.add(domain_model_mapping[domain.__name__]["table"])

        for table in output_table.keys():
            if should_reorg(reorg_block, table, self._service):
                self._should_reorg_type.add(output_table[table])
                self._should_reorg = True

    def _end(self):
        if self._reorg:
            for output in self.output_types:
                if output.type() not in self._should_reorg_type and output.type() in self._data_buff.keys():
                    self._data_buff.pop(output.type())

    # @deprecated
    # This function has been marked as deprecated in 0.6.0, and will be removed in 0.8.0.
    # Please move your data process logic into _process_function instead.
    @deprecated
    def _collect(self, **kwargs):
        pass

    # @deprecated
    # This function has been marked as deprecated in 0.6.0, and will be removed in 0.8.0.
    # Please move your data process batch logic into custom define function instead.
    @deprecated
    def _collect_batch(self, iterator):
        pass

    def _collect_item(self, key: str, data: Domain):
        with self.locks[key]:
            self._data_buff[key].append(data)

    def _collect_items(self, key, data_list: List[Domain]):
        with self.locks[key]:
            self._data_buff[key].extend(data_list)

    def _collect_domain(self, domain: Domain):
        with self.locks[domain.type()]:
            self._data_buff[domain.type()].append(domain)

    def _collect_domains(self, domains: List[Domain]):
        for domain in domains:
            self._collect_domain(domain)

    def _update_domains(self, domains: List[Domain]):
        key = domains[0].type()
        self._data_buff[key] = domains

    def _get_domain(self, domain):
        return self._data_buff[domain.type()] if domain.type() in self._data_buff else []

    def _get_domains(self, domains: list[Domain]):
        res = []
        for domain in domains:
            res += self._data_buff[domain.type()]
        return res

    # @deprecated
    # This function has been marked as deprecated in 0.6.0, and will be removed in 0.8.0.
    # Please move your data process logic into _process_function instead.
    @deprecated
    def _process(self, **kwargs):
        pass

    def _build_process_function_parameter(self):
        parameters = {}
        annotations = get_type_hints(self._process_function)
        for param, param_type in annotations.items():
            args_type = get_args(param_type)[0]
            if args_type.type() in self._data_buff:
                parameters[param] = self._data_buff[args_type.type()]
            else:
                parameters[param] = []

        return parameters

    def _process_function(self, **kwargs):
        pass

    def _export(self):
        items = []

        for output_type in self.output_types:
            if output_type in self._required_output_types:
                items.extend(self._data_buff[output_type.type()])

        for item_exporter in self._item_exporters:
            item_exporter.open()
            item_exporter.export_items(items, job_name=self.job_name)
            item_exporter.close()

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


def is_overwrite_process_function(cls: Type[BaseJob]):
    process_qualname = cls._process_function.__qualname__
    return process_qualname.startswith(cls.__name__)


def generate_dependency_types(cls: Type[BaseJob]):
    if not is_overwrite_process_function(cls):
        return

    annotations = get_type_hints(cls._process_function)

    dependency_types = []
    for param, param_type in annotations.items():
        if param == "return":
            continue
        origin_type = get_origin(param_type)
        if origin_type is not list:
            raise TypeError(
                f'The variable "{param}" define in _process function parameter list of {cls.__name__} '
                f"should be of type List[T] or list[T]."
            )

        args_types = get_args(param_type)

        if len(args_types) != 1:
            raise TypeError(
                f'The variable "{param}" define in _process function parameter list of {cls.__name__} '
                f"should only contain a single type in the list type."
            )

        args_type = args_types[0]
        if not issubclass(args_type, Domain) and args_type is not int:
            raise TypeError(
                f'The variable "{param}" define in _process function parameter list of {cls.__name__} '
                f"should have a list element type of int or a subclass of domain."
            )

        dependency_types.append(args_type)

    cls.dependency_types = dependency_types
