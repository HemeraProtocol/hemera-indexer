import copy
import inspect
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from queue import Queue
from typing import List, Type, Union, get_args, get_origin

from sqlalchemy import and_, func, select

from common.converter.pg_converter import domain_model_mapping
from common.models.blocks import Blocks
from common.models.logs import Logs
from common.models.transactions import Transactions
from common.services.postgresql_service import PostgreSQLService
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain import Domain, dict_to_dataclass
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.receipt import Receipt
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import BaseSourceJob
from indexer.specification.specification import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    FromAddressSpecification,
    ToAddressSpecification,
    TransactionFilterByLogs,
    TransactionFilterByTransactionInfo,
    TransactionHashSpecification,
)
from indexer.utils.collection_utils import distinct_collections_by_group, flatten

logger = logging.getLogger(__name__)


class PGSourceJob(BaseSourceJob):
    output_types = [
        Block,
        Transaction,
        Log,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._source_path = kwargs["config"].get("source_path", None)
        if self._source_path is None:
            raise FastShutdownError("-pg or --postgres-url is required to run PGSourceJob")
        self.pre_build = defaultdict(list)
        self.post_build = defaultdict()
        self.domain_mapping = defaultdict(dict)
        self.pg_datas = defaultdict(list)
        self._filters = flatten(kwargs.get("filters", []))
        self._is_filter = kwargs.get("is_filter", False)
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

        for output_type in self.output_types:
            self._dataclass_build_dependence(output_type, Domain)
        self.build_order = []
        self._calculate_build_queue()

    def _collect(self, **kwargs):
        if not self._service:
            self._service = PostgreSQLService(self._source_path) if self._source_path else None
        start_block = int(kwargs["start_block"])
        end_block = int(kwargs["end_block"])
        start_timestamp = self._query_timestamp_with_block(start_block)
        end_timestamp = self._query_timestamp_with_block(end_block)

        self.pg_datas.clear()
        if self._is_filter:
            filter_blocks = set()
            logs_transaction_hash = set()
            transactions_hash = set()
            for i, job_filter in enumerate(self._filters):
                if isinstance(job_filter, TransactionFilterByLogs):
                    log_filter = defaultdict(list)
                    for filter_param in job_filter.get_eth_log_filters_params():
                        param_address = filter_param.get("address", [])
                        param_topics = flatten(filter_param.get("topics", []))

                        if len(param_address) > 0:
                            log_filter["address"].extend(param_address)

                        if len(param_topics) > 0:
                            log_filter["topics"].extend(param_topics)

                    start_time = datetime.now()
                    logs = self._query_logs_filter(start_block, end_block, start_timestamp, end_timestamp, log_filter)
                    self.logger.info(
                        f"No.{i} filter: TransactionFilterByLogs finished. Took {datetime.now() - start_time}"
                    )
                    self.pg_datas[Logs].extend(logs)

                    for log in logs:
                        filter_blocks.add(log.block_number)
                        logs_transaction_hash.add(bytes_to_hex_str(log.transaction_hash))

                elif isinstance(job_filter, TransactionFilterByTransactionInfo):
                    transaction_filter = defaultdict(list)
                    for spe in job_filter.specifications:
                        params = spe.to_filter_params()
                        if isinstance(spe, TransactionHashSpecification) and params:
                            transaction_filter["hash"].extend(params["hashes"])
                            transactions_hash.add(params["hashes"])
                        elif isinstance(spe, FromAddressSpecification):
                            transaction_filter["from_address"].append(params["from_address"])
                        elif isinstance(spe, ToAddressSpecification):
                            transaction_filter["to_address"].append(params["to_address"])
                        else:
                            raise ValueError(f"Unsupported transaction filter type: {type(filter)}")

                    start_time = datetime.now()
                    transactions = self._query_transactions_filter(
                        start_block, end_block, start_timestamp, end_timestamp, transaction_filter
                    )
                    self.logger.info(
                        f"No.{i} filter: TransactionFilterByTransactionInfo finished. "
                        f"Took {datetime.now() - start_time}"
                    )

                    self.pg_datas[Transactions].extend(transactions)
                    for transaction in transactions:
                        filter_blocks.add(transaction.block_number)
                        transactions_hash.add(bytes_to_hex_str(transaction.hash))
                else:
                    raise ValueError(f"Unsupported filter type: {type(filter)}")

            if len(logs_transaction_hash) > 0:
                transaction_filter = {
                    "hash": list(logs_transaction_hash),
                    "from_address": [],
                    "to_address": [],
                }
                start_time = datetime.now()
                transactions = self._query_transactions_filter(
                    start_block, end_block, start_timestamp, end_timestamp, transaction_filter
                )
                self.logger.info(
                    f"Supplement transactions from filtered log list finished. Took {datetime.now() - start_time}"
                )
                self.pg_datas[Transactions].extend(transactions)

                for transaction in transactions:
                    filter_blocks.add(transaction.block_number)

            if len(transactions_hash) > 0:
                log_filter = {
                    "transaction_hash": list(transactions_hash),
                    "address": [],
                    "topics": [],
                }
                start_time = datetime.now()
                logs = self._query_logs_filter(start_block, end_block, start_timestamp, end_timestamp, log_filter)
                self.logger.info(
                    f"Supplement logs from filtered transaction list finished. Took {datetime.now() - start_time}"
                )
                self.pg_datas[Logs].extend(logs)

                for log in logs:
                    filter_blocks.add(log.block_number)

            self.pg_datas[Logs] = distinct_collections_by_group(
                collections=self.pg_datas[Logs], group_by=["transaction_hash", "log_index"]
            )
            self.pg_datas[Transactions] = distinct_collections_by_group(
                collections=self.pg_datas[Transactions], group_by=["hash"]
            )

            blocks = sorted(list(filter_blocks))
        else:
            blocks = list(range(start_block, end_block + 1))

        self._collect_from_pg(blocks, start_timestamp, end_timestamp)

    def _collect_from_pg(self, blocks, start_timestamp, end_timestamp):

        for output_type in self.output_types:
            table = domain_model_mapping[output_type]["table"]
            if len(self.pg_datas[table]) == 0:
                start_time = datetime.now()
                self.pg_datas[table] = self._query_with_blocks(table, blocks, start_timestamp, end_timestamp)
                self.logger.info(
                    f"Read {table.__tablename__} from postgres finished. Took {datetime.now() - start_time}"
                )

    def _process(self, **kwargs):
        self.domain_mapping.clear()
        for output_type in self.build_order:
            table = domain_model_mapping[output_type]["table"]
            domains = self._dataclass_build(self.pg_datas[table], output_type)
            if hasattr(table, "__query_order__"):
                domains.sort(key=lambda x: tuple(getattr(x, column.name) for column in table.__query_order__))
            self._data_buff[output_type.type()] = domains

    def _export(self):
        pass

    def _query_timestamp_with_block(self, block_number):
        session = self._service.get_service_session()
        try:
            timestamp = session.query(Blocks.timestamp).filter(Blocks.number == block_number).scalar()
        finally:
            session.close()

        return timestamp

    def _query_with_blocks(self, table, blocks, start_timestamp, end_timestamp):
        if len(blocks) == 0:
            return []

        session = self._service.get_service_session()
        unnest_query = select(func.unnest(blocks).label("block_number")).subquery()

        try:
            if hasattr(table, "number") and hasattr(table, "timestamp"):
                sub_table = (
                    select(table)
                    .filter(and_(table.timestamp >= start_timestamp, table.timestamp <= end_timestamp))
                    .subquery(table.__tablename__)
                )

                result = (
                    session.query(sub_table).join(unnest_query, sub_table.c.number == unnest_query.c.block_number).all()
                )
            elif hasattr(table, "block_number") and hasattr(table, "block_timestamp"):
                sub_table = (
                    select(table)
                    .filter(and_(table.block_timestamp >= start_timestamp, table.block_timestamp <= end_timestamp))
                    .subquery(table.__tablename__)
                )

                result = (
                    session.query(sub_table)
                    .join(unnest_query, sub_table.c.block_number == unnest_query.c.block_number)
                    .all()
                )
            else:
                result = []

        finally:
            session.close()

        return result

    def _query_logs_filter(self, start_block, end_block, start_timestamp, end_timestamp, log_filter):
        logs = []
        conditions = True
        session = self._service.get_service_session()

        try:

            if len(log_filter["address"]) > 0 and len(log_filter["topics"]) > 0:
                conditions = and_(
                    Logs.address.in_([hex_str_to_bytes(address) for address in set(log_filter["address"])]),
                    Logs.topic0.in_([hex_str_to_bytes(topic0) for topic0 in set(log_filter["topics"])]),
                )
            elif len(log_filter["address"]) > 0:
                conditions = Logs.address.in_([hex_str_to_bytes(address) for address in set(log_filter["address"])])
            elif len(log_filter["topics"]) > 0:
                conditions = Logs.topic0.in_([hex_str_to_bytes(topic0) for topic0 in set(log_filter["topics"])])

            if len(log_filter["address"]) > 0 or len(log_filter["topics"]) > 0:
                query_filter = and_(
                    Logs.block_timestamp >= start_timestamp,
                    Logs.block_timestamp <= end_timestamp,
                    conditions,
                    Logs.block_number >= start_block,
                    Logs.block_number <= end_block,
                )
                logs.extend(session.query(Logs).filter(query_filter).all())

            if len(log_filter["transaction_hash"]) > 0:
                conditions = Logs.transaction_hash.in_(
                    [hex_str_to_bytes(transaction_hash) for transaction_hash in set(log_filter["transaction_hash"])]
                )

                query_filter = and_(
                    Logs.block_timestamp >= start_timestamp,
                    Logs.block_timestamp <= end_timestamp,
                    conditions,
                    Logs.block_number >= start_block,
                    Logs.block_number <= end_block,
                )
                logs.extend(session.query(Logs).filter(query_filter).all())
        finally:
            session.close()

        return logs

    def _query_transactions_filter(self, start_block, end_block, start_timestamp, end_timestamp, transaction_filter):
        transactions = []
        session = self._service.get_service_session()

        try:

            if len(transaction_filter["hash"]) > 0:
                conditions = Transactions.hash.in_(
                    [hex_str_to_bytes(transaction_hash) for transaction_hash in set(transaction_filter["hash"])]
                )
                query_filter = and_(
                    Transactions.block_timestamp >= start_timestamp,
                    Transactions.block_timestamp <= end_timestamp,
                    conditions,
                    Transactions.block_number >= start_block,
                    Transactions.block_number <= end_block,
                )
                transactions.extend(session.query(Transactions).filter(query_filter).all())

            if len(transaction_filter["from_address"]) > 0:
                conditions = Transactions.from_address.in_(
                    [hex_str_to_bytes(from_address) for from_address in set(transaction_filter["from_address"])]
                )
                query_filter = and_(
                    Transactions.block_timestamp >= start_timestamp,
                    Transactions.block_timestamp <= end_timestamp,
                    conditions,
                    Transactions.block_number >= start_block,
                    Transactions.block_number <= end_block,
                )
                transactions.extend(session.query(Transactions).filter(query_filter).all())

            if len(transaction_filter["to_address"]) > 0:
                conditions = Transactions.to_address.in_(
                    [hex_str_to_bytes(to_address) for to_address in set(transaction_filter["to_address"])]
                )
                query_filter = and_(
                    Transactions.block_timestamp >= start_timestamp,
                    Transactions.block_timestamp <= end_timestamp,
                    conditions,
                    Transactions.block_number >= start_block,
                    Transactions.block_number <= end_block,
                )
                transactions.extend(session.query(Transactions).filter(query_filter).all())

            if (
                len(transaction_filter["hash"]) == 0
                and len(transaction_filter["from_address"]) == 0
                and len(transaction_filter["to_address"]) == 0
            ):
                query_filter = and_(
                    Transactions.block_timestamp >= start_timestamp,
                    Transactions.block_timestamp <= end_timestamp,
                    Transactions.block_number >= start_block,
                    Transactions.block_number <= end_block,
                )
                transactions.extend(session.query(Transactions).filter(query_filter).all())

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
            self.domain_mapping[output_type] = {transaction.hash: transaction for transaction in transactions}
            if Block in self.output_types:
                for transaction in transactions:
                    self.domain_mapping[Block][transaction.block_hash].transactions.append(transaction)

            return transactions

        def build_log():
            logs = [table_to_dataclass(data, Log) for data in pg_datas]
            if Transaction in self.output_types:
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
    if hasattr(row_instance, "__table__"):
        for column in row_instance.__table__.columns:
            if column.name == "meta_data":
                meta_data_json = getattr(row_instance, column.name)
                if meta_data_json:
                    for key in meta_data_json:
                        dict_instance[key] = meta_data_json[key]
            else:
                value = getattr(row_instance, column.name)
                dict_instance[column.name] = convert_value(value)
    else:
        for column, value in row_instance._asdict().items():
            dict_instance[column] = convert_value(value)

    domain = dict_to_dataclass(dict_instance, cls)
    if cls is Transaction:
        domain.fill_with_receipt(Receipt.from_pg(dict_instance))

    return domain


def convert_value(value):
    if isinstance(value, datetime):
        return int(round(value.timestamp()))
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return bytes_to_hex_str(value)
    elif isinstance(value, list):
        return [convert_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: convert_value(v) for k, v in value.items()}
    else:
        return value
