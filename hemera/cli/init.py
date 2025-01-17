import logging
import os.path

import click

from hemera.cli.options.schedule import metrics_config
from hemera.cli.options.storage import postgres, postgres_initial
from hemera.common.logo import print_logo
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.file_utils import get_project_root
from hemera.common.utils.format_utils import to_camel_case, to_space_camel_case
from hemera.indexer.utils.metrics_persistence import BasePersistence, init_persistence
from hemera.indexer.utils.template_generator import TemplateGenerator

logger = logging.getLogger("Init Client")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@metrics_config
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
    "--metrics",
    is_flag=True,
    required=False,
    help="The --metrics flag triggers the metrics' persistence data initialization process. ",
)
@postgres
@postgres_initial
def init(jobs, db, metrics, postgres_url, db_version, init_schema, instance_name, persistence_type):
    print_logo()
    if db:
        init_schema = True
        PostgreSQLService(jdbc_url=postgres_url, db_version=db_version, init_schema=init_schema)
        logger.info("Database successfully initialized.")

    if jobs:
        jobs = [job.lower() for job in jobs.split(",")]
        jobs_space_initialize_before_check(jobs)

    if metrics:
        config = {}
        if postgres_url:
            service = PostgreSQLService(jdbc_url=postgres_url)
            config["db_service"] = service
        persistence = init_persistence(instance_name=instance_name, persistence_type=persistence_type, config=config)
        persistence.init()
        logger.info(f"The instance: {instance_name}'s metrics has been successfully initialized.")


def jobs_space_initialize_before_check(jobs):
    project_root = get_project_root()
    custom_jobs_path = os.path.join(project_root, "hemera_udf")
    exists_job = os.listdir(custom_jobs_path)

    empty_generator = TemplateGenerator()
    init_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "hemera/resource/template/custom_init.example")
    )
    job_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "hemera/resource/template/export_custom_job.example")
    )
    domain_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "hemera/resource/template/custom_domain.example")
    )
    model_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "hemera/resource/template/custom_module.example")
    )
    namespace_generator = TemplateGenerator(
        template_file=os.path.join(project_root, "hemera/resource/template/custom_api_namespace.example")
    )

    for job in jobs:
        if job in exists_job:
            logger.error(f"In the folder './hemera_udf/', custom job named {job} already exists.")
            continue

        custom_job_path = os.path.join(custom_jobs_path, job)

        init_generator.add_replacements(key="${job_name}", value=job)
        init_generator.add_replacements(key="${entity_name}", value=job.upper())
        init_generator.generate_file(target_path=os.path.join(custom_job_path, "__init__.py"))

        job_generator.add_replacements(key="${job}", value=job)
        job_generator.add_replacements(key="${job_name}", value=to_camel_case(job))
        job_generator.generate_file(target_path=os.path.join(custom_job_path, f"export_{job}_job.py"))

        domain_generator.generate_file(target_path=os.path.join(custom_job_path, "domains.py"))

        model_generator.add_replacements(key="${job}", value=job)
        model_generator.generate_file(target_path=os.path.join(custom_job_path, "models", f"{job}_module.py"))
        empty_generator.generate_file(target_path=os.path.join(custom_job_path, "models", "__init__.py"))

        namespace_generator.add_replacements(key="${job}", value=job)
        namespace_generator.add_replacements(key="${job_descript}", value=to_space_camel_case(job))
        namespace_generator.generate_file(target_path=os.path.join(custom_job_path, "endpoint", "__init__.py"))
        empty_generator.generate_file(target_path=os.path.join(custom_job_path, "endpoint", "routes.py"))

        logger.info(f"{job} successfully initialized.")
