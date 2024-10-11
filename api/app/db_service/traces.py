from common.models import db
from common.models.traces import Traces
from common.utils.db_utils import build_entities
from common.utils.format_utils import hex_str_to_bytes


def get_traces_by_transaction_hash(transaction_hash, columns="*"):
    transaction_hash = hex_str_to_bytes(transaction_hash)
    entities = build_entities(Traces, columns)

    traces = (
        db.session.query(Traces)
        .with_entities(*entities)
        .filter(Traces.transaction_hash == transaction_hash)
        .order_by(Traces.trace_address)
        .all()
    )

    return traces


def get_traces_by_condition(filter_condition=None, columns="*", limit=1):
    entities = build_entities(Traces, columns)

    traces = db.session.query(Traces).with_entities(*entities).filter(filter_condition).limit(limit).all()

    return traces
