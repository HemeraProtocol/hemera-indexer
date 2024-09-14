from datetime import datetime

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import get_yesterday_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


def aggregates_yesterday_job(chain_name: str, postgres_url: str, dblink_url: str):
    print('---executing aggregates job---')
    start_date, end_date = get_yesterday_date()
    db_service = PostgreSQLService(postgres_url)

    version = int(datetime.now().timestamp())

    config = {"db_service": db_service, "chain_name": chain_name, 'dblink_url': dblink_url, 'version': version}

    dispatcher = AggregatesDispatcher(config)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)
