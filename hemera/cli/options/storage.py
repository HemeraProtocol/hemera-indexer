import click


def cache_target(options):
    options = click.option(
        "--cache",
        default="memory",
        show_default=True,
        type=str,
        envvar="CACHE_SERVICE",
        help="How to store the cache data."
        "e.g redis. means cache data will store in redis, redis://localhost:6379"
        "or memory. means cache data will store in memory, memory",
    )(options)

    return options


def sink_target(options):
    options = click.option(
        "-o",
        "--output",
        type=str,
        envvar="OUTPUT",
        help="The output selection."
        "Print to console e.g. console; "
        "or postgresql e.g. postgres"
        "or local json file e.g. jsonfile://your-file-path; "
        "or local csv file e.g. csvfile://your-file-path; "
        "or both. e.g. console,jsonfile://your-file-path,csvfile://your-file-path",
    )(options)

    return options


def file_size(options):
    options = click.option(
        "--blocks-per-file",
        default=1000,
        show_default=True,
        type=int,
        envvar="BLOCKS_PER_FILE",
        help="How many blocks data was written to each file",
    )(options)

    return options


def postgres(options):
    options = click.option(
        "-pg",
        "--postgres-url",
        type=str,
        required=False,
        envvar="POSTGRES_URL",
        help="The required postgres connection url."
        "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
    )(options)

    return options


def postgres_initial(options):
    options = click.option(
        "-v",
        "--db-version",
        default="head",
        show_default=True,
        type=str,
        envvar="DB_VERSION",
        help="The database version to initialize the database. using the alembic script's revision ID to "
        "specify a version. "
        "e.g. head, indicates the latest version."
        "or base, indicates the empty database without any table.",
    )(options)

    options = click.option(
        "-i",
        "--init-schema",
        is_flag=True,
        required=False,
        show_default=True,
        envvar="INIT_SCHEMA",
        help="Whether to automatically run database migration scripts to update the database to the specify version.",
    )(options)

    return options


def pid_file_storage(options):
    options = click.option(
        "--pid-file",
        show_default=True,
        type=str,
        envvar="PID_FILE",
        help="Pid file",
    )(options)

    return options
