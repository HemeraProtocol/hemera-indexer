import logging
from datetime import datetime, timezone

from sqlalchemy import and_, func, insert, literal, select

from hemera.common.models import HemeraModel
from hemera.common.models.blocks import Blocks
from hemera.common.models.fix_record import FixRecord
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.exception_control import RetriableError


def set_reorg_sign(jobs, block_number, service):
    from hemera.common.converter.pg_converter import domain_model_mapping

    conn = service.get_conn()
    cur = conn.cursor()
    try:
        table_done = set()
        for job in jobs:
            for output in job.output_types:
                model = domain_model_mapping[output.__name__]
                table = model["table"]
                if table.__name__ in table_done:
                    continue

                table_done.add(table.__name__)
                if hasattr(table, "reorg"):
                    update_stmt = (
                        f"UPDATE {table.__tablename__} "
                        + f"SET reorg=TRUE, update_time='{datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp())}'"
                    )

                    if hasattr(table, "number"):
                        update_stmt += f"WHERE number={block_number}"
                    elif hasattr(table, "block_number"):
                        update_stmt += f"WHERE block_number={block_number}"
                    else:
                        update_stmt = None
                        logging.warning(
                            f"Reorging table: {table} has no block number info, "
                            f"could not complete reorg action, "
                            f"reorging will be skipped this table."
                        )

                    if update_stmt:
                        cur.execute(update_stmt)
        conn.commit()
    except Exception as e:
        logging.error(e)
        raise RetriableError(e)
    finally:
        service.release_conn(conn)


def should_reorg(block_number: int, table: HemeraModel, service: PostgreSQLService):
    if not hasattr(table, "reorg"):
        return False
    condition = None
    if hasattr(table, "number"):
        condition = and_(table.reorg == True, table.number == block_number)
    elif hasattr(table, "block_number"):
        condition = and_(table.reorg == True, table.block_number == block_number)
    else:
        return False

    session = service.get_service_session()
    try:
        result = session.query(table).filter(condition).first()
    finally:
        session.close()
    return result is not None


def check_reorg(service: PostgreSQLService, check_range: int = None):
    check_where = and_(Blocks.reorg == False, Blocks.number >= check_range) if check_range else Blocks.reorg == False

    inner_query = (
        select(
            Blocks.number,
            Blocks.hash,
            Blocks.parent_hash,
            func.lag(Blocks.number, 1).over(order_by=Blocks.number).label("parent_number"),
            func.lag(Blocks.hash, 1).over(order_by=Blocks.number).label("lag_hash"),
        )
        .where(check_where)
        .alias("align_table")
    )

    select_stmt = select(
        inner_query.c.number.label("start_block_number"),
        (inner_query.c.number + 1).label("last_fixed_block_number"),
        literal(5).label("remain_process"),
        literal("submitted").label("job_status"),
    ).where(
        and_(
            inner_query.c.parent_hash != inner_query.c.lag_hash, inner_query.c.number == inner_query.c.parent_number + 1
        )
    )

    insert_stmt = insert(FixRecord).from_select(
        ["start_block_number", "last_fixed_block_number", "remain_process", "job_status"], select_stmt
    )

    db_session = service.get_service_session()
    db_session.execute(insert_stmt)
    db_session.commit()
    db_session.close()
