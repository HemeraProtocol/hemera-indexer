from datetime import datetime

from common.services.postgresql_service import PostgreSQLService
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


def run_aggregate_job(chain_name: str, postgres_url: str, start_date: str, end_date: str):
    db_service = PostgreSQLService(postgres_url)
    version = int(datetime.now().timestamp())
    config = {"db_service": db_service, "chain_name": chain_name, 'version': version}

    dispatcher = AggregatesDispatcher(config)
    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)
