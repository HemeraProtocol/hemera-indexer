import copy
import inspect
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from queue import Queue
from typing import List, Type, Union, get_args, get_origin

from sqlalchemy import text, or_, and_, select, func

from common.converter.pg_converter import domain_model_mapping
from common.models.logs import Logs
from common.models.transactions import Transactions
from common.utils.exception_control import FastShutdownError
from indexer.domain import Domain, dict_to_dataclass
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.receipt import Receipt
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import BaseSourceJob
from indexer.specification.specification import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    TransactionFilterByLogs,
    TransactionFilterByTransactionInfo,
    TransactionHashSpecification, FromAddressSpecification, ToAddressSpecification,
)

from indexer.utils.utils import flatten

logger = logging.getLogger(__name__)


class PGSourceJob(BaseSourceJob):
    output_types = [
        Block,
        Transaction,
        Log,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pre_build = defaultdict(list)
        self.post_build = defaultdict()
        self.domain_mapping = defaultdict(dict)
        self.pg_datas = defaultdict(list)
        self._filters = flatten(kwargs.get("filters", []))
        self._is_filter = kwargs.get("is_filter", False)
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

        if self._service is None:
            raise FastShutdownError("-pg or --postgres-url is required to run PGSourceJob")

        self.build_dependency = {}
        for output_type in self.output_types:
            self._dataclass_build_dependence(output_type, Domain)
        self.build_order = []
        self._calculate_build_queue()

        self.has_logs_filter = False
        self.has_transaction_filter = False
        self.log_filter = {"address": [], "topics": [], "transaction_hash": []}
        self.transaction_filter = {"hash": [], "from_address": [], "to_address": []}
        if self._is_filter:
            self._extract_filter_params()

    def _collect(self, **kwargs):
        start_block = int(kwargs["start_block"])
        end_block = int(kwargs["end_block"])

        self.pg_datas.clear()
        if self._is_filter:
            filter_blocks = set()
            extra_transaction = set()
            if self.has_logs_filter:
                logs = self._query_logs_filter(start_block, end_block, self.log_filter)
                self.pg_datas[Logs] = logs

                for log in logs:
                    filter_blocks.add(log.block_number)
                    extra_transaction.add('0x' + log.transaction_hash.hex())

            extra_trx_size = len(extra_transaction)
            if self.has_transaction_filter or extra_trx_size > 0:
                transaction_filter = copy.deepcopy(self.transaction_filter)
                transaction_filter['hash'].extend(list(extra_transaction))
                transactions = self._query_transactions_filter(start_block, end_block, transaction_filter)
                self.pg_datas[Transactions] = transactions

                for transaction in transactions:
                    filter_blocks.add(transaction.block_number)
                    extra_transaction.add('0x' + transaction.hash.hex())

                # if more transaction found, re-fetch logs
                if extra_trx_size != len(extra_transaction):
                    log_filter = copy.deepcopy(self.log_filter)
                    log_filter['transaction_hash'].extend(list(extra_transaction))
                    logs = self._query_logs_filter(start_block, end_block, log_filter)
                    self.pg_datas[Logs] = logs

            blocks = sorted(list(filter_blocks))
        else:
            blocks = list(range(start_block, end_block + 1))

        self._collect_from_pg(blocks)

    def _collect_from_pg(self, blocks):
        session = self._service.get_service_session()

        try:
            for output_type in self.output_types:
                table = domain_model_mapping[output_type.__name__]["table"]
                if len(self.pg_datas[table]) == 0:
                    self.pg_datas[table] = self._query_with_blocks(table, blocks)
        finally:
            session.close()

    def _process(self, **kwargs):
        for output_type in self.build_order:
            table = domain_model_mapping[output_type.__name__]["table"]
            domains = self._dataclass_build(self.pg_datas[table], output_type)
            self._data_buff[output_type.type()] = domains

    def _export(self):
        pass

    def _query_with_blocks(self, table, blocks):
        if len(blocks) == 0:
            return []

        session = self._service.get_service_session()
        unnest_query = select(func.unnest(blocks).label('block_number')).subquery()
        try:
            if hasattr(table, "number"):
                result = (session.query(table)
                          .join(unnest_query, table.number == unnest_query.c.block_number)
                          .order_by(*table.__query_order__)
                          .all())
            else:
                result = (session.query(table)
                          .join(unnest_query, table.block_number == unnest_query.c.block_number)
                          .order_by(*table.__query_order__)
                          .all())

        finally:
            session.close()

        return result

    def _query_logs_filter(self, start_block, end_block, log_filter):
        query_filter = None

        if len(log_filter["address"]) > 0:
            query_filter = or_(query_filter,
                               Logs.address.in_(
                                   [bytes.fromhex(address[2:]) for address in set(log_filter["address"])]
                               ))

        if len(log_filter["topics"]) > 0:
            query_filter = or_(query_filter,
                               Logs.topic0.in_(
                                   [bytes.fromhex(topic0[2:]) for topic0 in set(log_filter["topics"])]
                               ))

        if len(log_filter["transaction_hash"]) > 0:
            query_filter = or_(query_filter,
                               Logs.transaction_hash.in_(
                                   [bytes.fromhex(transaction_hash[2:])
                                    for transaction_hash in set(log_filter["transaction_hash"])]
                               ))

        query_filter = and_(query_filter, Logs.block_number >= start_block, Logs.block_number <= end_block)

        session = self._service.get_service_session()
        try:
            logs = (session.query(Logs)
                    .filter(query_filter)
                    .order_by(*Logs.__query_order__)
                    .all())
        finally:
            session.close()
        return logs

    def _query_transactions_filter(self, start_block, end_block, transaction_filter):
        query_filter = None

        if len(transaction_filter["hash"]) > 0:
            query_filter = or_(query_filter,
                               Transactions.hash.in_(
                                   [bytes.fromhex(transaction_hash[2:])
                                    for transaction_hash in set(transaction_filter["hash"])]
                               ))

        if len(transaction_filter["from_address"]) > 0:
            query_filter = or_(query_filter,
                               Transactions.from_address.in_(
                                   [bytes.fromhex(from_address[2:])
                                    for from_address in set(transaction_filter["from_address"])]
                               ))

        if len(transaction_filter["to_address"]) > 0:
            query_filter = or_(query_filter,
                               Transactions.to_address.in_(
                                   [bytes.fromhex(to_address[2:])
                                    for to_address in set(transaction_filter["to_address"])]
                               ))

        query_filter = and_(query_filter,
                            Transactions.block_number >= start_block,
                            Transactions.block_number <= end_block)

        session = self._service.get_service_session()
        try:
            transactions = (session.query(Transactions)
                            .filter(query_filter)
                            .order_by(*Transactions.__query_order__)
                            .all())
        finally:
            session.close()
        return transactions

    def _dataclass_build(self, pg_datas, output_type):

        def build_block():
            blocks = [table_to_dataclass(data, Block) for data in pg_datas]
            self.domain_mapping[output_type] = {block.hash: block for block in blocks}
            for block in blocks:
                block.transactions = []

            return blocks

        def build_transaction():
            transactions = [table_to_dataclass(data, Transaction) for data in pg_datas]
            self.domain_mapping[output_type] = {transactions.hash: transactions for transactions in transactions}
            for transaction in transactions:
                self.domain_mapping[Block][transaction.block_hash].transactions.append(transaction)

            return transactions

        def build_log():
            logs = [table_to_dataclass(data, Log) for data in pg_datas]
            for log in logs:
                self.domain_mapping[Transaction][log.transaction_hash].receipt.logs.append(log)

            return logs

        special_build = {
            Block: build_block,
            Transaction: build_transaction,
            Log: build_log,
        }

        if output_type in special_build:
            domains = special_build[output_type]()
        else:
            domains = [table_to_dataclass(data, output_type) for data in pg_datas]

        return domains

    def _dataclass_build_dependence(self, cls_type: Type[Domain], target_type):
        field_types = {f.name: f.type for f in cls_type.__dataclass_fields__.values()}

        for field, field_type in field_types.items():
            is_dependent, dependent_type = check_dependency(field_type, Domain)
            if is_dependent:
                self.pre_build[cls_type].append(dependent_type)
                self.post_build[dependent_type] = cls_type
                if dependent_type not in self.output_types:
                    self._dataclass_build_dependence(dependent_type, target_type)

    def _calculate_build_queue(self):
        build_queue = Queue()
        un_build_outputs = copy.copy(self.output_types)
        while len(un_build_outputs) > 0:
            for output_type in un_build_outputs:
                if output_type not in self.post_build:
                    build_queue.put(output_type)
                    un_build_outputs.remove(output_type)

                    if output_type in self.pre_build:
                        for cls_type in self.pre_build[output_type]:
                            if cls_type in self.post_build:
                                del self.post_build[cls_type]
                                if cls_type is Receipt:
                                    for post_type in self.pre_build[cls_type]:
                                        del self.post_build[post_type]

        while not build_queue.empty():
            self.build_order.append(build_queue.get())

    def _extract_filter_params(self):
        for filter in self._filters:
            if isinstance(filter, TransactionFilterByLogs):
                for filter_param in filter.get_eth_log_filters_params():
                    self.log_filter["address"].extend(filter_param["address"])
                    self.log_filter["topics"].extend(flatten(filter_param["topics"]))
                self.has_logs_filter = True

            elif isinstance(filter, TransactionFilterByTransactionInfo):
                for spe in filter.specifications:
                    params = spe.to_filter_params()
                    if isinstance(spe, TransactionHashSpecification) and params:
                        self.transaction_filter["hash"].extend(params["hashes"])
                        self.log_filter["transaction_hash"].extend(params["hashes"])
                        self.has_logs_filter = True
                    elif isinstance(spe, FromAddressSpecification):
                        self.transaction_filter["from_address"].append(params["from_address"])
                    elif isinstance(spe, ToAddressSpecification):
                        self.transaction_filter["to_address"].append(params["to_address"])
                    else:
                        raise ValueError(f"Unsupported transaction filter type: {type(filter)}")
                self.has_transaction_filter = True
            else:
                raise ValueError(f"Unsupported filter type: {type(filter)}")


def check_dependency(column_type, target_type) -> (bool, object):
    is_dependent = False
    if get_origin(column_type) is Union:
        for arg in get_args(column_type):
            is_dependent, dependent_type = check_dependency(arg, target_type)
            if is_dependent:
                return is_dependent, dependent_type
        return is_dependent, None

    if get_origin(column_type) is list or column_type is List:
        if get_args(column_type):
            return check_dependency(get_args(column_type)[0], target_type)
        return False, None

    if column_type is target_type:
        return True, target_type

    if inspect.isclass(column_type) and issubclass(column_type, target_type):
        return True, column_type

    return False, None


def table_to_dataclass(row_instance, cls):
    """
    Converts row of table to a dataclass instance, handling nested structures.

    Args:
        row_instance (HemeraModel): The input data structure.
        cls: The dataclass type to convert to.

    Returns:
        An instance of the dataclass which is corresponding to table in the definition.
    """

    dict_instance = {}
    for column in row_instance.__table__.columns:
        if column.name == "meta_data":
            meta_data_json = getattr(row_instance, column.name)
            if meta_data_json:
                for key in meta_data_json:
                    dict_instance[key] = meta_data_json[key]
        else:
            attr = getattr(row_instance, column.name)
            if isinstance(attr, datetime):
                dict_instance[column.name] = int(round(attr.timestamp()))
            elif isinstance(attr, Decimal):
                dict_instance[column.name] = float(attr)
            elif isinstance(attr, bytes):
                dict_instance[column.name] = "0x" + attr.hex()
            else:
                dict_instance[column.name] = attr

    domain = dict_to_dataclass(dict_instance, cls)
    if cls is Transaction:
        domain.fill_with_receipt(Receipt.from_pg(dict_instance))

    return domain
