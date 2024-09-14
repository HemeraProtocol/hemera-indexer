import copy
import inspect
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from queue import Queue
from typing import List, Type, Union, get_args, get_origin

from common.converter.pg_converter import domain_model_mapping
from common.services.postgresql_service import PostgreSQLService
from indexer.domain import Domain, dict_to_dataclass
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.receipt import Receipt
from indexer.domain.transaction import Transaction
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseSourceJob
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy

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

    def _collect(self, **kwargs):
        start_block = int(kwargs["start_block"])
        end_block = int(kwargs["end_block"])

        self.pg_datas = self._collect_from_pg(start_block, end_block)

    def _collect_from_pg(self, start_block, end_block):
        collect_results = {}
        session = self._service.get_service_session()
        try:
            for output_type in self.output_types:
                table = domain_model_mapping[output_type.__name__]["table"]

                if hasattr(table, "number"):
                    results = (
                        session.query(table)
                        .filter(table.number >= start_block, table.number <= end_block)
                        .order_by(*table.__query_order__)
                        .all()
                    )
                else:
                    results = (
                        session.query(table)
                        .filter(table.block_number >= start_block, table.block_number <= end_block)
                        .order_by(*table.__query_order__)
                        .all()
                    )

                collect_results[table] = results
        finally:
            session.close()

        return collect_results

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
        un_build_outputs = copy.copy(output_types)
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
