import logging

import yaml

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.job_list_generator import JobListGenerator
from indexer.aggr_jobs.utils import get_yesterday_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def parse_crontab(expression):
    fields = expression.split()

    if len(fields) != 5:
        raise ValueError("Invalid crontab expression, it must contain 5 fields.")

    minute, hour, day, month, day_of_week = fields

    parsed_fields = {"minute": minute, "hour": hour, "day": day, "month": month, "day_of_week": day_of_week}

    return parsed_fields


def parse_aggregate_schedule():
    with open("/app/config.yaml", "r") as file:
        config = yaml.safe_load(file)

    common_config = config["common_config"]
    default_schedule_time = common_config["schedule_time"]

    jobs = config["jobs"]

    result_jobs = []
    for job_name, job_config in jobs.items():
        initialization_jobs = job_config.get("initialization_jobs", [])
        disorder_jobs = job_config.get("disorder_jobs", [])
        order_jobs = job_config.get("order_jobs", [])

        job_list_generator = JobListGenerator(job_name=job_name, initialization_jobs=initialization_jobs,
                                              disorder_jobs=disorder_jobs,
                                              order_jobs=order_jobs)

        job_config_config = job_config.get('config')
        if job_config_config:
            schedule_time = job_config_config.get("schedule_time", default_schedule_time)
        else:
            schedule_time = default_schedule_time

        result_jobs.append(
            {'schedule_time': schedule_time, 'job_list_generator': job_list_generator})

    return result_jobs


def aggregates_yesterday_job(chain_name, job_list_generator, postgres_url, dblink_url):
    job_name = job_list_generator.job_name

    logger.info(f"Job {job_name} executed")

    start_date, end_date = get_yesterday_date()
    db_service = PostgreSQLService(postgres_url)

    config = {"db_service": db_service, "chain_name": chain_name, "dblink_url": dblink_url}

    dispatcher = AggregatesDispatcher(config, job_list_generator)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date)
