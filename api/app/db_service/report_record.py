#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/29 下午4:50
Author  : xuzh
Project : hemera_indexer
"""
from sqlalchemy import case, desc, text
from sqlalchemy.sql import and_

from common.models import db
from common.models.report_records import ReportRecords
from common.utils.db_utils import build_entities
from indexer.modules.custom.avs_operator.models.hemera_avs_log import HemeraAvsOperatorLog
from indexer.modules.custom.avs_operator.models.task import AggregatorTask


def get_report_record(columns="*", conditions=None, limit=None, offset=None, fill_with_status=False):
    entities = build_entities(ReportRecords, columns)

    statement = db.session.query(ReportRecords).with_entities(*entities).order_by(desc(ReportRecords.create_time))
    if conditions is not None:
        statement = statement.filter(conditions)

    if limit:
        statement = statement.limit(limit)

    if offset:
        statement = statement.offset(offset)

    if fill_with_status:
        page_query = statement.subquery("paged_records")
        status_table = (
            db.session.query(
                HemeraAvsOperatorLog.tx_hash,
                case((AggregatorTask.tx_hash is not None, "pass"), else_="failed").label("status"),
            )
            .outerjoin(AggregatorTask, HemeraAvsOperatorLog.msg_hash == AggregatorTask.alert_hash)
            .subquery("status_table")
        )

        records = (
            db.session.query(page_query, status_table.c.status.label("status"))
            .outerjoin(status_table, page_query.c.transaction_hash == status_table.c.tx_hash)
            .all()
        )
    else:
        records = statement.all()
    return records


def get_report_record_cnt(conditions=None):
    statement = db.session.query(ReportRecords)

    if conditions is not None:
        statement = statement.filter(conditions)

    count = statement.count()
    return count


def get_report_record_by_condition(block_number, dataclass, columns="*", limit=None, offset=None):
    if block_number:
        block_conditions = and_(
            ReportRecords.start_block_number <= block_number,
            ReportRecords.end_block_number >= block_number,
        )
    else:
        block_conditions = True

    if dataclass:
        # dataclass_conditions = [
        #     ReportRecords.report_details.contains([{'dataClass': code}])
        #     for code in dataclass
        # ]
        # dataclass_conditions = func.jsonb_path_exists(
        #     ReportRecords.report_details,
        #     '$[*] ? (@.dataClass == $values)',
        #     vars=func.jsonb_build_object('values', dataclass)
        # )
        dataclass_conditions = text(
            """
                    EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(report_details) obj
                        WHERE obj->>'dataClass' = ANY(:dataclass)
                    )
                """
        ).bindparams(dataclass=dataclass)
    else:
        dataclass_conditions = True

    conditions = and_(block_conditions, dataclass_conditions) if block_number or dataclass else None

    return get_report_record(columns=columns, conditions=conditions, limit=limit, offset=offset)
