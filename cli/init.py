import logging
import os.path
from shutil import copy
from typing import List

import click

from common.models import HemeraModel, model_path_patterns
from common.services.postgresql_service import PostgreSQLService
from common.utils.file_utils import get_project_root
from common.utils.format_utils import to_camel_case
from common.utils.module_loading import import_string, scan_subclass_by_path_patterns
from indexer.utils.template_generator import TemplateGenerator

logger = logging.getLogger("Init Client")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--jobs",
    type=str,
    default=None,
    required=False,
    help="The custom job's name that needs to initialized. "
    "If you need to initialize multiple jobs at the same time, please separate by ','"
    "e.g. ens,deposit_to_l2",
)
@click.option(
    "--db",
    is_flag=True,
    required=False,
    help="The --db flag triggers the database initialization process. ",
)
@click.option(
    "-pg",
    "--postgres-url",
    type=str,
    required=False,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
)
@click.option(
    "-v",
    "--version",
    type=str,
    default="head",
    show_default=True,
    required=False,
    help="The database version that would be initialized. "
    "By using default value 'head', database would be initialized to the latest version."
    "To make this option work, either -i or --init must be used.",
)
def init(jobs, db, postgres_url, version):
    if db:
        service = PostgreSQLService(jdbc_url=postgres_url, db_version=version, init_schema=True)
        logger.info("Database successfully initialized.")

    if jobs:
        jobs = [job.lower() for job in jobs.split(",")]
        jobs_space_initialize_before_check(jobs)


def jobs_space_initialize_before_check(jobs):
    project_root = get_project_root()
    custom_jobs_path = os.path.join(project_root, "custom_jobs")
    exists_job = os.listdir(custom_jobs_path)

    job_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "resource/template/export_custom_job.example")
    )
    domain_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "resource/template/custom_domain.example")
    )
    model_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "resource/template/custom_module.example")
    )

    for job in jobs:
        if job in exists_job:
            logger.error(f"In the folder './custom_jobs/', custom job named {job} already exists.")
            continue

        custom_job_path = os.path.join(custom_jobs_path, job)
        job_generator.add_replacements(key="{$job_name}", value=to_camel_case(job))
        job_generator.generate_file(target_path=os.path.join(custom_job_path, f"export_{job}_job.py"))

        domain_generator.generate_file(target_path=os.path.join(custom_job_path, "domains", f"{job}_domain.py"))

        model_generator.add_replacements(key="${job}", value=job)
        model_generator.add_replacements(key="${domain_file}", value=f"{job}_domain")
        model_generator.generate_file(target_path=os.path.join(custom_job_path, "models", f"{job}_module.py"))

        logger.info(f"{job} successfully initialized.")
