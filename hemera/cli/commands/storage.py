import click


def cache_target(commands):
    commands = click.option(
        "--cache",
        default="memory",
        show_default=True,
        type=str,
        envvar="CACHE_SERVICE",
        help="How to store the cache data."
        "e.g redis. means cache data will store in redis, redis://localhost:6379"
        "or memory. means cache data will store in memory, memory",
    )(commands)

    return commands


def sink_target(commands):
    commands = click.option(
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
    )(commands)

    return commands


def file_size(commands):
    commands = click.option(
        "--blocks-per-file",
        default=1000,
        show_default=True,
        type=int,
        envvar="BLOCKS_PER_FILE",
        help="How many blocks data was written to each file",
    )(commands)

    return commands


def postgres(commands):
    commands = click.option(
        "-pg",
        "--postgres-url",
        type=str,
        required=False,
        envvar="POSTGRES_URL",
        help="The required postgres connection url."
        "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
    )(commands)

    return commands


def postgres_initial(commands):
    commands = click.option(
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
    )(commands)

    commands = click.option(
        "-i",
        "--init-schema",
        is_flag=True,
        required=False,
        show_default=True,
        envvar="INIT_SCHEMA",
        help="Whether to automatically run database migration scripts to update the database to the specify version.",
    )(commands)

    return commands


def pid_file_storage(commands):
    commands = click.option(
        "--pid-file",
        default=None,
        show_default=True,
        type=str,
        envvar="PID_FILE",
        help="Pid file",
    )(commands)

    return commands
