import logging
from datetime import datetime, timezone

from sqlalchemy import and_

from common.models import __models_imports, HemeraModel
from common.services.postgresql_service import PostgreSQLService
from common.utils.module_loading import import_string


def set_reorg_sign(block_number, service):
    conn = service.get_conn()
    cur = conn.cursor()
    for model, path in __models_imports.items():
        table = import_string(f"{path}.{model}")
        if hasattr(table, "reorg"):
            update_stmt = f"UPDATE {table.__tablename__} " + \
                          f"SET reorg=TRUE, update_time='{datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp())}'"

            if hasattr(table, "number"):
                update_stmt += f"WHERE number={block_number}"
            elif hasattr(table, "block_number"):
                update_stmt += f"WHERE block_number={block_number}"
            else:
                update_stmt = None
                logging.warning(f"Reorging table: {table} has no block number info, "
                                f"could not complete reorg action, "
                                f"reorging will be skipped this table.")

            if update_stmt:
                cur.execute(update_stmt)

    conn.commit()


def should_reorg(block_number: int, table: HemeraModel, service: PostgreSQLService):
    session = service.get_service_session()
    try:
        result = (
            session.query(table)
            .filter(
                and_(
                    table.block_number == block_number,
                    table.reorg == True
                ))
            .first()
        )
    finally:
        session.close()
    return result is None
