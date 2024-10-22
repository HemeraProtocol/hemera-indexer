from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.job_list_generator import JobListGenerator
from indexer.aggr_jobs.utils import get_yesterday_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


def parse_crontab(expression):
    fields = expression.split()

    if len(fields) != 5:
        raise ValueError("Invalid crontab expression, it must contain 5 fields.")

    minute, hour, day, month, day_of_week = fields

    parsed_fields = {"minute": minute, "hour": hour, "day": day, "month": month, "day_of_week": day_of_week}

    return parsed_fields


def aggregates_yesterday_job(chain_name, job_name, postgres_url, dblink_url):
    print("---executing aggregates job---")
    start_date, end_date = get_yesterday_date()
    db_service = PostgreSQLService(postgres_url)

    config = {"db_service": db_service, "chain_name": chain_name, "dblink_url": dblink_url}
    job_list = JobListGenerator(job_name)

    dispatcher = AggregatesDispatcher(config, job_list)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)
