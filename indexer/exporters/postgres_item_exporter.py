import binascii
import collections
import io
import logging
import re
from contextlib import contextmanager
from datetime import datetime
from typing import List, Type, Optional, Any

import psycopg2
import sqlalchemy
from dateutil.tz import tzlocal
from psycopg2 import Binary
from sqlalchemy import text, MetaData, Table, inspect, func, Text, ARRAY, Numeric, Integer, Float, BigInteger, DateTime, \
    String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql.base import BYTEA
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.exc import DBAPIError
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy.sql.functions import Function

from common.models import HemeraModel
from indexer.domain import Domain
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type
from common.converter.pg_converter import domain_model_mapping

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 10000


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):

        self.service = service

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        session = self.service.get_service_session()
        try:
            items_grouped_by_type = group_by_item_type(items)
            tables = []
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)

                if item_group:
                    pg_config = domain_model_mapping[item_type.__name__]

                    table = pg_config['table']
                    do_update = pg_config['conflict_do_update']
                    update_strategy = pg_config['update_strategy']
                    converter = pg_config['converter']

                    data = [converter(table, item, do_update) for item in item_group]
                    split_data = [data[i: i + COMMIT_BATCH_SIZE] for i in range(0, len(data), COMMIT_BATCH_SIZE)]

                    if do_update:
                        for batch in split_data:
                            statement = insert(table).values(batch)
                            statement = self.on_conflict_do_update(item_type, table, statement, update_strategy)
                            session.execute(statement)
                            session.commit()

                    else:
                        for batch in split_data:
                            statement = insert(table).values(batch).on_conflict_do_nothing()
                            session.execute(statement)
                            session.commit()

                    tables.append(table.__tablename__)

        except Exception as e:
            # print(e)
            logger.error(f"Error exporting items:{e}")
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            session.close()
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to table {} end, Item count: {}, Took {}"
            .format(", ".join(tables), len(items), (end_time - start_time)))

    @staticmethod
    def on_conflict_do_update(domain: Type[Domain], model: Type[HemeraModel], statement, where_clause=None):
        pk_list = []
        for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
            if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
                for column in constraint.columns:
                    pk_list.append(column.name)

        update_set = {}
        for exc in statement.excluded:
            if exc.name not in pk_list and exc.name in domain.__annotations__.keys():
                update_set[exc.name] = exc

        if where_clause:
            where_clause = text(where_clause)

        statement = statement.on_conflict_do_update(index_elements=pk_list, set_=update_set, where=where_clause)
        return statement


class PostgresItemExporterV2(BaseExporter):
    def __init__(self, service):
        self.service = service

    @contextmanager
    def get_session(self):
        session = self.service.get_service_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        try:
            items_grouped_by_type = group_by_item_type(items)

            # with ThreadPoolExecutor() as executor:
            #     futures = []
            #     for item_type, item_group in items_grouped_by_type.items():
            #         if item_group:
            #             futures.append(executor.submit(self.process_item_group, item_type, item_group))
            #
            #     tables = [future.result() for future in futures]

            for item_type, item_group in items_grouped_by_type.items():
                if item_group:
                    self.process_item_group(item_type, item_group)

        except Exception as e:
            logger.error(f"Error exporting items: {e}")
            raise Exception("Error exporting items")

        end_time = datetime.now(tzlocal())
        # logger.info(
        #     "Exporting items to table {} end, Item count: {}, Took {}"
        #     .format(", ".join(tables), len(items), (end_time - start_time)))

    def process_item_group(self, item_type, item_group):
        with self.get_session() as session:
            pg_config = domain_model_mapping[item_type.__name__]
            table = pg_config['table']
            do_update = pg_config['conflict_do_update']
            update_strategy = pg_config['update_strategy']
            converter = pg_config['converter']

            data = [converter(table, item, do_update) for item in item_group]

            if do_update:
                self.upsert_data(session, item_type, table, data, update_strategy)
            else:
                self.copy_data(session, table, data)

            return table.__tablename__

    def copy_data(self, session, table, data):
        if isinstance(table, str):
            table_name = table
            columns_info = self.get_columns_info(session, table_name)
        else:
            table = table.__table__ if isinstance(table, type) else table
            table_name = table.name
            columns_info = {c.name: c.type for c in table.columns}

        prepared_data = []
        for row in data:
            prepared_row = {key: PostgresItemExporterV2.format_value(value, columns_info.get(key)) for key, value in row.items()}
            prepared_data.append(prepared_row)

        with session.connection().connection.cursor() as cursor:
            cursor.execute(f"SELECT to_regclass('{table_name}')")
            if cursor.fetchone()[0] is None:
                raise ValueError(f"Table {table_name} does not exist")

            columns = prepared_data[0].keys()
            copy_command = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"

            from io import StringIO
            import csv

            csv_file = StringIO()
            writer = csv.DictWriter(csv_file, fieldnames=columns)
            writer.writerows(prepared_data)
            csv_file.seek(0)

            try:
                cursor.copy_expert(copy_command, csv_file)
            except psycopg2.Error as e:
                logger.error(f"Error during COPY operation: {e}")
                raise

        session.commit()
    @staticmethod
    def format_value(value, column_type):
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return r'\N'  # 使用 \N 表示 NULL

        if getattr(column_type, '__visit_name__', None) == 'BYTEA':
            hex_value = '\\x' + binascii.hexlify(value).decode('ascii')
            return hex_value
        if isinstance(column_type, (Numeric, Integer, Float)):
            return str(value) if value != '' else r'\N'
        if isinstance(column_type, ARRAY):
            return PostgresItemExporterV2.format_array(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        if isinstance(value, Function):
            return PostgresItemExporterV2.evaluate_function(value)
        return str(value)

    @staticmethod
    def format_array(value):
        if value is None or value == []:
            return r'\N'
        if isinstance(value, list):
            return '{' + ','.join(PostgresItemExporterV2.format_value(v, None) for v in value) + '}'
        return str(value)

    def get_columns_info(self, session, table_name):
        # 获取表的列信息
        columns_info = {}
        with session.connection().connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            for column_name, data_type in cursor.fetchall():
                columns_info[column_name] = self.map_pg_type_to_sa_type(data_type)
        return columns_info

    @staticmethod
    def map_pg_type_to_sa_type(pg_type):
        # 映射 PostgreSQL 类型到 SQLAlchemy 类型
        type_map = {
            'bytea': BYTEA,
            'integer': Integer,
            'bigint': BigInteger,
            'numeric': Numeric,
            'double precision': Float,
            'timestamp without time zone': DateTime,
            'ARRAY': ARRAY,
            # 添加其他需要的类型映射
        }
        return type_map.get(pg_type.lower(), String)

    @staticmethod
    def evaluate_function(function_obj):
        if function_obj.name == 'to_timestamp':
            # 获取 to_timestamp 的第一个参数
            timestamp_value = function_obj.clauses.clauses[0].value
            if isinstance(timestamp_value, int):
                # 如果是整数，假设为UNIX时间戳
                return datetime.utcfromtimestamp(timestamp_value).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp_value, str):
                # 如果是字符串，假设为日期时间字符串
                return datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        # 你可以在这里处理更多的 Function 对象
        return None

    @staticmethod
    def clean_csv_value(value: Optional[Any]) -> str:
        if value is None:
            return r'NULL'
        return str(value).replace('\n', '\\n').replace('|', '\|').replace('\x00', '')

    @staticmethod
    def create_temp_table(session, table):
        temp_table_name = f"temp_{table.__tablename__}"

        # 使用 IF NOT EXISTS 子句创建临时表
        create_temp_table_sql = f"""
        CREATE TEMPORARY TABLE IF NOT EXISTS {temp_table_name} (
            LIKE {table.__tablename__} INCLUDING ALL
        ) ON COMMIT PRESERVE ROWS
        """
        session.execute(text(create_temp_table_sql))
        session.commit()  # 立即提交以确保其他连接可以看到这个临时表

        # 返回临时表名称而不是表对象
        return temp_table_name

    @staticmethod
    def get_primary_keys(table):
        return [key.name for key in table.__table__.primary_key]

    def upsert_data(self, session, item_type, table, data, update_strategy):
        temp_table_name = self.create_temp_table(session, table)
        try:
            self.copy_data(session, temp_table_name, data)

            pk_list = self.get_primary_keys(table)
            if isinstance(table, type):
                table = table.__table__
            update_columns = [c.name for c in table.columns if c.name not in pk_list]

            merge_statement = self.create_merge_statement(table, temp_table_name, pk_list, update_columns)
            session.execute(text(merge_statement))
        except Exception as e:
            logger.error(f"Error during upsert operation: {e}")
            raise
        finally:
            # 总是尝试删除临时表，即使发生错误
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
                session.commit()
            except Exception as e:
                logger.error(f"Error dropping temporary table: {e}")

    @staticmethod
    def create_merge_statement(target_table, source_table_name, pk_list, update_columns):
        target_name = target_table.__tablename__ if hasattr(target_table, '__tablename__') else target_table.name

        merge_stmt = f"""
        MERGE INTO {target_name} AS target
        USING {source_table_name} AS source
        ON {' AND '.join(f'target.{pk} = source.{pk}' for pk in pk_list)}
        WHEN MATCHED THEN
            UPDATE SET {', '.join(f'{col} = source.{col}' for col in update_columns)}
        WHEN NOT MATCHED THEN
            INSERT ({', '.join(target_table.columns.keys())})
            VALUES ({', '.join(f'source.{col}' for col in target_table.columns.keys())})
        """
        return merge_stmt

