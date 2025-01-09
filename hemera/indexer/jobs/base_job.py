import logging
import threading
from collections import defaultdict
from datetime import datetime
from typing import Generic, List, Type, TypeVar, Union, get_args, get_origin, get_type_hints

from deprecated import deprecated
from web3 import Web3

from hemera.common.utils.exception_control import FastShutdownError, RetriableError
from hemera.common.utils.format_utils import to_snake_case
from hemera.indexer.domains import Domain
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.utils.buffer_service import BufferService
from hemera.indexer.utils.reorg import should_reorg

T = TypeVar("T")


class Collector(Generic[T]):

    def __init__(self, job, collect_types: List[Domain]):
        self.job = job
        self.collect_types = set(collect_types)

    def check_collect_type(self, cls):
        if cls not in self.collect_types:
            raise ValueError(
                f"Collector only collects the following types of data: {[self.collect_types]}, "
                f"the data type given now is {cls}"
            )

    def collect_item(self, key: str, data: Domain):
        if data is None:
            return

        self.check_collect_type(type(data))
        with self.job._data_buff_lock[key]:
            self.job._data_buff[key].append(data)

    def collect_items(self, key, datas: List[Domain]):
        if datas is None or len(datas) == 0:
            return

        self.check_collect_type(type(datas[0]))
        with self.job._data_buff_lock[key]:
            self.job._data_buff[key].extend(datas)

    def collect_domain(self, domain: Domain):
        if domain is None:
            return

        self.check_collect_type(type(domain))
        self.collect(domain)

    def collect_domains(self, domains: List[Domain]):
        if domains is None or len(domains) == 0:
            return

        self.check_collect_type(type(domains[0]))
        self.collects(domains)

    def collect(self, domain: Domain):
        if domain is None:
            return

        self.check_collect_type(type(domain))
        with self.job._data_buff_lock[domain.type()]:
            self.job._data_buff[domain.type()].append(domain)

    def collects(self, domains: List[Domain]):
        if domains is None or len(domains) == 0:
            return

        self.check_collect_type(type(domains[0]))
        with self.job._data_buff_lock[domains[0].type()]:
            self.job._data_buff[domains[0].type()].extend(domains)

    def update(self, domains: List[Domain]):
        self.job._update_domains(domains)


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
    _data_buff: Union[dict, BufferService] = defaultdict(list)
    _data_buff_lock = defaultdict(threading.Lock)

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
        self._batch_web3_provider = kwargs["batch_web3_provider"]
        self._web3 = Web3(Web3.HTTPProvider(self._batch_web3_provider.endpoint_uri))
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_batch = kwargs["batch_size"] > 1 if kwargs.get("batch_size") else False
        self._reorg = kwargs["reorg"] if kwargs.get("reorg") else False

        self._chain_id = kwargs.get("chain_id") or (self._web3.eth.chain_id if self._batch_web3_provider else None)

        self._should_reorg = False
        self._should_reorg_type = set()
        self._service = kwargs["config"].get("db_service", None)
        self.collector = Collector(self, self.output_types)

        job_name_snake = to_snake_case(self.job_name)
        self.user_defined_config = kwargs["config"][job_name_snake] if kwargs["config"].get(job_name_snake) else {}

    def run(self, **kwargs):
        try:
            start_block = kwargs["start_block"]
            end_block = kwargs["end_block"]

            self._start(**kwargs)

            if self.able_to_reorg and self._reorg:
                start_time = datetime.now()
                self.logger.info(f"Stage _pre_reorg starting.")
                self._pre_reorg(**kwargs)
                self.logger.info(f"Stage _pre_reorg finished. Took {datetime.now() - start_time}")

            if not self._reorg or self._should_reorg:
                if is_overwrite_udf(self.__class__):
                    parameters = self._build_udf_parameter()
                    self._udf(**parameters)
                else:
                    self._collect(**kwargs)
                    self._process(**kwargs)

            if not self._reorg or not issubclass(self.__class__, BaseSourceJob):
                if (
                    type(self._data_buff) is BufferService
                    and not self._data_buff.is_shutdown()
                    and not self._data_buff.check_and_flush(
                        start_block=start_block,
                        end_block=end_block,
                        job_name=self.job_name,
                        output_types=[output.type() for output in self.output_types],
                    )
                ):
                    raise RetriableError(f"Job {self.job_name} export error.")

        finally:
            self._end()

    def _start(self, **kwargs):
        for dataclass in self.output_types:
            self._data_buff[dataclass.type()].clear()

    def _pre_reorg(self, **kwargs):
        from hemera.common.converter.pg_converter import domain_model_mapping

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
    # This function has been marked as deprecated in 0.6.0, and will be removed in 1.1.0.
    # Please move your data process logic into _udf instead.
    @deprecated
    def _collect(self, **kwargs):
        pass

    # @deprecated
    # This function has been marked as deprecated in 0.6.0, and will be removed in 1.1.0.
    # Please move your data process batch logic into custom define function instead.
    @deprecated
    def _collect_batch(self, iterator):
        pass

    def _collect_item(self, key, data: Domain):
        with self._data_buff_lock[key]:
            self._data_buff[key].append(data)

    def _collect_items(self, key, data_list: List[Domain]):
        with self._data_buff_lock[key]:
            self._data_buff[key].extend(data_list)

    def _collect_domain(self, domain: Domain):
        with self._data_buff_lock[domain.type()]:
            self._data_buff[domain.type()].append(domain)

    def _collect_domains(self, domains: List[Domain]):
        for domain in domains:
            self._collect_domain(domain)

    def _update_domains(self, domains: List[Domain]):
        if not domains:
            return
        self._data_buff[domains[0].type()] = domains

    def _get_domain(self, domain):
        return self._data_buff[domain.type()] if domain.type() in self._data_buff else []

    def _get_domains(self, domains: list[Domain]):
        res = []
        for domain in domains:
            res += self._data_buff[domain.type()]
        return res

    # @deprecated
    # This function has been marked as deprecated in 0.6.0, and will be removed in 1.1.0.
    # Please move your data process logic into _udf instead.
    @deprecated
    def _process(self, **kwargs):
        pass

    def _build_udf_parameter(self):
        parameters = {}
        annotations = get_type_hints(self._udf)
        for param, param_type in annotations.items():
            if param == "output":
                continue
            args_type = get_args(param_type)[0]
            if args_type.type() in self._data_buff.keys():
                parameters[param] = self._data_buff[args_type.type()]
            else:
                parameters[param] = []

        parameters["output"] = self.collector
        return parameters

    def _udf(self, **kwargs):
        pass

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


def is_overwrite_udf(cls: Type[BaseJob]):
    process_qualname = cls._udf.__qualname__
    return process_qualname.startswith(cls.__name__)


def generate_dependency_types(cls: Type[BaseJob]):
    if not is_overwrite_udf(cls):
        return

    annotations = get_type_hints(cls._udf)

    if "output" not in annotations:
        raise TypeError(f"Missing output collector: output in _udf function parameter list of {cls.__name__}.")

    dependency_types = []
    output_types = []
    for param, param_type in annotations.items():
        if param == "return":
            continue

        if param == "output":
            output_types = varify_output_hints(cls.__name__, param_type)
        else:
            args_type = varify_input_hints(cls.__name__, param, param_type)
            dependency_types.append(args_type)

    cls.dependency_types = dependency_types
    cls.output_types = output_types


def varify_input_hints(job_name, param, param_type):
    origin_type = get_origin(param_type)
    if origin_type is not list:
        raise TypeError(
            f'The variable "{param}" define in {job_name}\'s _udf function parameter list '
            f"should be of type List[T] or list[T]."
        )

    args_types = get_args(param_type)

    if len(args_types) != 1:
        raise TypeError(
            f'The variable "{param}" define in {job_name}\'s _udf function parameter list '
            f"should only contain a single type in the list type."
        )

    args_type = args_types[0]
    if not issubclass(args_type, Domain) and args_type is not int:
        raise TypeError(
            f'The variable "{param}" define in {job_name}\'s _udf function parameter list '
            f"should have a list element type of int or a subclass of domain."
        )

    return args_type


def varify_output_hints(job_name, param_type):
    output_types = []

    origin_type = get_origin(param_type)
    if origin_type is not Collector:
        raise TypeError(
            f'The variable "output" define in {job_name}\'s _udf function parameter list '
            f"should be of type indexer.jobs.base_job.Collector. \n"
            f"Now it is of type {origin_type}."
        )

    arg_types = get_args(param_type)
    if get_origin(arg_types[0]) is not Union and not issubclass(arg_types[0], Domain):
        raise TypeError(
            f'The variable "output" define in {job_name}\'s _udf function parameter list '
            f"should be Collector[Domain] or Collector[Union[DomainA, DomainB]]. \n"
        )

    if get_origin(arg_types[0]) is Union:
        for arg_type in get_args(arg_types[0]):
            if not issubclass(arg_type, Domain):
                raise TypeError(
                    f'The collector "output" define in {job_name}\'s _udf function parameter list '
                    f"only collects data of type domain subclass."
                )
            output_types.append(arg_type)
    elif issubclass(arg_types[0], Domain):
        output_types.append(arg_types[0])

    return output_types
