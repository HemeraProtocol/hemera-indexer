import copy
import inspect
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from queue import Queue
from typing import List, Type, Union, get_args, get_origin

from sqlalchemy import text, or_, and_

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

    def _collect(self, **kwargs):
        start_block = int(kwargs["start_block"])
        end_block = int(kwargs["end_block"])

        has_logs_filter = False
        has_transaction_filter = False
        if self._is_filter:
            filter_blocks = set()
            log_filter = {"address": [], "topics": []}
            transaction_filter = {"hash": [], "from_address": [], "to_address": []}
            for filter in self._filters:
                if isinstance(filter, TransactionFilterByLogs):
                    for filter_param in filter.get_eth_log_filters_params():
                        log_filter["address"].extend(filter_param["address"])
                        log_filter["topics"].extend(flatten(filter_param["topics"]))
                    has_logs_filter = True

                elif isinstance(filter, TransactionFilterByTransactionInfo):
                    for spe in filter.specifications:
                        params = spe.to_filter_params()
                        if isinstance(spe, TransactionHashSpecification) and params:
                            transaction_filter["hash"].extend(params["hashes"])
                        elif isinstance(spe, FromAddressSpecification):
                            transaction_filter["from_address"].append(params["from_address"])
                        elif isinstance(spe, ToAddressSpecification):
                            transaction_filter["to_address"].append(params["to_address"])
                        else:
                            raise ValueError(f"Unsupported transaction filter type: {type(filter)}")
                    has_transaction_filter = True
                else:
                    raise ValueError(f"Unsupported filter type: {type(filter)}")

            if has_logs_filter:
                logs = self.query_logs_filter(start_block, end_block, log_filter)
                self.pg_datas[Logs] = logs

                for log in logs:
                    filter_blocks.add(log['block_number'])
                    transaction_filter["hash"].append(log["transaction_hash"])

            if has_transaction_filter:
                transactions = self.query_transactions_filter(start_block, end_block, transaction_filter)
                self.pg_datas[Transactions] = transactions

                for transaction in transactions:
                    filter_blocks.add(transaction['block_number'])

            blocks = list(filter_blocks)
        else:
            blocks = list(range(start_block, end_block + 1))

        self._collect_from_pg(blocks)

    def _collect_from_pg(self, blocks):
        session = self._service.get_service_session()

        try:
            for output_type in self.output_types:
                table = domain_model_mapping[output_type.__name__]["table"]
                if len(self.pg_datas[table]) == 0:
                    self.pg_datas[table] = self.query_with_blocks(table, blocks)
        finally:
            session.close()

    def _process(self, **kwargs):
        self.build_dependency = {}
        for output_type in self.output_types:
            self.dataclass_build_dependence(output_type, Domain)

        output_build_queue = self.calculate_build_queue()
        while not output_build_queue.empty():
            output_type = output_build_queue.get()
            table = domain_model_mapping[output_type.__name__]["table"]
            domains = self.dataclass_build(self.pg_datas[table], output_type)
            self._data_buff[output_type.type()] = domains

    def _export(self):
        pass

    def query_with_blocks(self, table, blocks):
        session = self._service.get_service_session()

        try:
            if hasattr(table, "number"):
                stmt = text(
                    f"""
                SELECT
                    {table.__tablename__}.*
                FROM {table.__tablename__}
                JOIN unnest(:blocks) AS v(block_number) ON {table.__tablename__}.number = v.block_number
                """
                )
            else:
                stmt = text(
                    f"""
                SELECT
                    {table.__tablename__}.*
                FROM {table.__tablename__}
                JOIN unnest(:blocks) AS v(block_number) ON {table.__tablename__}.block_number = v.block_number
                    """
                )

            result = session.execute(stmt, {"blocks": blocks}).fetchall()
        finally:
            session.close()

        return result

    def query_logs_filter(self, start_block, end_block, log_filter):
        query_filter = and_(Logs.block_number >= start_block, Logs.block_number <= end_block)

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

        session = self._service.get_service_session()
        try:
            logs = (session.query(Logs)
                    .filter(query_filter)
                    .order_by(*Logs.__query_order__)
                    .all())
        finally:
            session.close()
        return logs

    def query_transactions_filter(self, start_block, end_block, transaction_filter):
        query_filter = and_(Transactions.block_number >= start_block, Transactions.block_number <= end_block)

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

        session = self._service.get_service_session()
        try:
            transactions = (session.query(Transactions)
                            .filter(query_filter)
                            .order_by(*Transactions.__query_order__)
                            .all())
        finally:
            session.close()
        return transactions

    def dataclass_build(self, pg_datas, output_type):

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

    def dataclass_build_dependence(self, cls_type: Type[Domain], target_type):
        field_types = {f.name: f.type for f in cls_type.__dataclass_fields__.values()}

        for field, field_type in field_types.items():
            is_dependent, dependent_type = check_dependency(field_type, Domain)
            if is_dependent:
                self.pre_build[cls_type].append(dependent_type)
                self.post_build[dependent_type] = cls_type
                if dependent_type not in self.output_types:
                    self.dataclass_build_dependence(dependent_type, target_type)

    def calculate_build_queue(self):
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
        return build_queue


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
