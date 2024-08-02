#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/2 17:10
# @Author  will
# @File  postgres_item_exporter_v2.py
# @Brief
import binascii
import csv
import io
import logging
from datetime import datetime
from typing import List

import psycopg2
from sqlalchemy import (
    ARRAY,
    Float,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.sql.functions import Function

from common.converter.pg_converter import domain_model_mapping
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 10000
class PostgresItemExporterV2(BaseExporter):
    def __init__(self, service):
        self.service = service

    def export_items(self, items):
        session = self.service.get_service_session()
        try:
            items_grouped_by_type = group_by_item_type(items)
            tables = []

            for item_type, item_group in items_grouped_by_type.items():
                if item_group:
                    try:
                        table = self.process_item_group(session, item_type, item_group)
                        tables.append(table)
                        logger.info(f"Processed item group: {item_type}")
                    except Exception as e:
                        logger.error(f"Error processing item group {item_type}: {e}")

            logger.info(f"Exported items to tables: {', '.join(tables)}, Item count: {len(items)}")

        except Exception as e:
            logger.error(f"Error exporting items: {e}")
            raise Exception("Error exporting items")
        finally:
            session.close()

    def process_item_group(self, session, item_type, item_group):

        pg_config = domain_model_mapping[item_type.__name__]
        table = pg_config['table']
        do_update = pg_config['conflict_do_update']
        update_strategy = pg_config['update_strategy']
        converter = pg_config['converter']

        data = [converter(table, item, do_update) for item in item_group]
        split_data = [data[i: i + COMMIT_BATCH_SIZE] for i in range(0, len(data), COMMIT_BATCH_SIZE)]
        for batch in split_data:
            self.upsert_data(session, item_type, table, batch, update_strategy)

        # if do_update:
        #     self.upsert_data(session, item_type, table, data, update_strategy)
        # else:
        #     self.copy_data(session, table.__tablename__, table, data)

        return table.__tablename__

    def copy_data(self, session, table_name, raw_table, data):

        table = raw_table.__table__
        columns_info = {c.name: c.type for c in table.columns}

        prepared_data = []
        for row in data:
            prepared_row = {key: self.format_value(value, columns_info.get(key)) for key, value in row.items()}
            prepared_data.append(prepared_row)

        with session.connection().connection.cursor() as cursor:
            cursor.execute(f"SELECT to_regclass('{table_name}')")
            if cursor.fetchone()[0] is None:
                raise ValueError(f"Table {table_name} does not exist")

            columns = prepared_data[0].keys()
            copy_command = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"

            csv_file = io.StringIO()
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
            return r'\N'
        if getattr(column_type, '__visit_name__', None) == 'BYTEA':
            hex_value = '\\x' + binascii.hexlify(value).decode('ascii')
            return hex_value
        if isinstance(column_type, (Numeric, Integer, Float)):
            return str(value) if value != '' else r'\N'
        if isinstance(column_type, ARRAY) or isinstance(column_type, List):
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

    @staticmethod
    def evaluate_function(function_obj):
        if function_obj.name == 'to_timestamp':
            timestamp_value = function_obj.clauses.clauses[0].value
            if isinstance(timestamp_value, int):
                return datetime.utcfromtimestamp(timestamp_value).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp_value, str):
                return datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        return None

    @staticmethod
    def create_temp_table(session, table):
        temp_table_name = f"temp_{table.__tablename__}"
        create_temp_table_sql = f"""
        CREATE TEMPORARY TABLE IF NOT EXISTS {temp_table_name} (
            LIKE {table.__tablename__} INCLUDING ALL
        ) ON COMMIT PRESERVE ROWS
        """
        session.execute(text(create_temp_table_sql))
        session.commit()
        return temp_table_name

    @staticmethod
    def get_primary_keys(table):
        return [key.name for key in table.__table__.primary_key]

    def upsert_data(self, session, item_type, table, data, update_strategy):
        temp_table_name = self.create_temp_table(session, table)
        try:
            self.copy_data(session, temp_table_name, table, data)

            pk_list = self.get_primary_keys(table)

            update_columns = self.exclude_generate_columns(table)

            merge_statement = self.create_merge_statement(table, temp_table_name, pk_list, update_columns)
            session.execute(text(merge_statement))
        except Exception as e:
            logger.error(f"Error during upsert operation: {e}")
            raise e
        finally:
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
                session.commit()
            except Exception as e:
                logger.error(f"Error dropping temporary table: {e}")

    def exclude_generate_columns(self, table):
        pk_list = self.get_primary_keys(table)
        if isinstance(table, type):
            t = table.__table__
        else:
            t = table
        update_columns = []
        for c in t.columns:
            if c.name not in pk_list:
                if not c.server_default and not c.server_onupdate:
                    update_columns.append(c.name)
        return update_columns

    @staticmethod
    def is_generate_column(c):
        return c.server_default or c.server_onupdate

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
            INSERT ({', '.join([k.name for k in target_table.__table__.columns if not PostgresItemExporterV2.is_generate_column(k)])})
            VALUES ({', '.join(f'source.{col.name}' for col in target_table.__table__.columns if not PostgresItemExporterV2.is_generate_column(col))})
        """
        return merge_stmt