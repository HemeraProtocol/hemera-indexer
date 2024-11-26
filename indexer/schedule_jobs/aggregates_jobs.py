from datetime import datetime

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import get_yesterday_date, get_current_date, read_yaml_file
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


def aggregates_yesterday_job(chain_name: str, postgres_url: str, dblink_url: str, config_file):
    start_date, end_date = get_yesterday_date()
    print(f'---executing yesterday aggregates job-----{start_date}----{end_date}-')


    version = int(datetime.now().timestamp())

    jobs_dict = read_yaml_file(config_file)

    db_service = PostgreSQLService(postgres_url)
    config = {"db_service": db_service, "chain_name": chain_name, 'dblink_url': dblink_url, 'version': version, 'jobs_dict': jobs_dict}

    dispatcher = AggregatesDispatcher(config)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)


def aggregates_current_date_job(chain_name: str, postgres_url: str, dblink_url: str, config_file):
    start_date, end_date = get_current_date()
    print(f'---executing current_date aggregates job----{start_date} {end_date}--')

    version = int(datetime.now().timestamp())
    jobs_dict = read_yaml_file(config_file)

    db_service = PostgreSQLService(postgres_url)
    config = {"db_service": db_service, "chain_name": chain_name, 'dblink_url': dblink_url, 'version': version,
              'jobs_dict': jobs_dict}

    dispatcher = AggregatesDispatcher(config)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)
