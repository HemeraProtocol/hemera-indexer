import re

from alembic import context
from alembic.autogenerate import rewriter
from alembic.operations import ops
from sqlalchemy import engine_from_config, pool
from sqlalchemy.sql.schema import SchemaItem

from hemera.common.models import db
from hemera.common.utils.module_loading import import_submodules

# Make sure everything is imported so that alembic can find it all
# import_all_models()
import_submodules("hemera.common.models")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

IGNORE_DB_TABLE = []
PARTITION_TABLES = []


def table_able_to_track(**kwargs) -> bool:
    name = kwargs["name"]
    reflected = kwargs["reflected"]
    if reflected:
        return not any(name.startswith(table) for table in IGNORE_DB_TABLE)
    return True


def do_not_track_partition_table(**kwargs) -> bool:
    name = kwargs["name"]
    reflected = kwargs["reflected"]
    object_type = kwargs["object_type"]

    if reflected and object_type == "table":
        partition_patterns = [
            re.compile(r"^(.+)_partition_\d{6}$"),
            re.compile(r"^(.+)_(\d{4})_(\d{2})$"),
            re.compile(r"^(.+)_p(\d{4})_(\d{2})$"),
            re.compile(r"^(.+)_p(\d{1,2})$"),
            re.compile(r"^(.+)_default$"),
        ]
        for pattern in partition_patterns:
            match = pattern.match(name)

            if match:
                return False
    return True


tracking_list = [table_able_to_track, do_not_track_partition_table]

writer = rewriter.Rewriter()


@writer.rewrites(ops.CreateTableOp)
def rewrite_create_table(context, revision, op):
    op.if_not_exists = True
    return op


@writer.rewrites(ops.CreateIndexOp)
def rewrite_create_index(context, revision, op):
    op.if_not_exists = True
    return op


@writer.rewrites(ops.DropTableOp)
def rewrite_drop_table(context, revision, op):
    op.if_exists = True
    return op


@writer.rewrites(ops.DropIndexOp)
def rewrite_drop_index(context, revision, op):
    op.if_exists = True
    return op


def custom_table_tracking(
    obj: SchemaItem, name: str, object_type: str, reflected: bool, compare_to: SchemaItem
) -> bool:
    for tracking in tracking_list:
        if not tracking(obj=obj, name=name, object_type=object_type, reflected=reflected, compare_to=compare_to):
            return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=custom_table_tracking,
        process_revision_directives=writer,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=custom_table_tracking,
            process_revision_directives=writer,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
