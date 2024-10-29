#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/29 下午4:50
Author  : xuzh
Project : hemera_indexer
"""
from sqlalchemy.sql import and_

from common.models import db
from common.models.report_records import ReportRecords
from common.utils.db_utils import build_entities


def get_report_record(block_number, columns="*"):
    entities = build_entities(ReportRecords, columns)

    record = (
        db.session.query(ReportRecords)
        .with_entities(*entities)
        .filter(
            and_(
                ReportRecords.start_block_number <= block_number,
                ReportRecords.end_block_number >= block_number,
            )
        )
        .all()
    )

    return record
