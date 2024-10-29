#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/29 上午10:38
Author  : xuzh
Project : hemera_indexer
"""
import enum

from sqlalchemy import Column, Enum, Index, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, JSON, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class ReportStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    NO_RECEIPT = "no_receipt"
    TRANSACTION_FAILED = "transaction_failed"


class ReportRecord(HemeraModel):
    __tablename__ = "report_record"
    report_id = Column(INTEGER, primary_key=True)
    chain_id = Column(INTEGER)
    start_block_number = Column(BIGINT)
    end_block_number = Column(BIGINT)
    runtime_code_hash = Column(BYTEA)
    report_details = Column(JSON)
    transaction_hash = Column(BYTEA)
    report_status = Column(Enum(ReportStatus, name="report_status"), nullable=False, default=ReportStatus.PENDING)
    exception = Column(VARCHAR)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())


Index(
    "report_record_start_end_block_number_index",
    desc(ReportRecord.start_block_number),
    desc(ReportRecord.end_block_number),
)
