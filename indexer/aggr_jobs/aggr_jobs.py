from datetime import datetime

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import get_current_date, get_yesterday_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


def run_aggregate_job(chain_name: str, postgres_url: str, start_date: str, end_date: str):
    db_service = PostgreSQLService(postgres_url)
    version = int(datetime.now().timestamp())
    config = {"db_service": db_service, "chain_name": chain_name, 'version': version}

    dispatcher = AggregatesDispatcher(config)
    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)


def run_today_or_yesterday_aggregate_job(chain_name: str, postgres_url: str, day_str: str):
    if day_str == 'today':
        start_date, end_date = get_current_date()
    elif day_str == 'yesterday':
        start_date, end_date = get_yesterday_date()

    run_aggregate_job(chain_name, postgres_url, start_date, end_date)
