import threading
from queue import Queue

from sqlalchemy.dialects.postgresql import insert

from hemera.common.models.records import ExceptionRecords

LOG_BUFFER_SIZE = 5000


class ExceptionRecorder(object):
    _instance = None

    _queue_lock = threading.Lock()
    _flush_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._service = None
        self._log_buffer = Queue()
        self._multicall_log_buffer = Queue()

    def init_pg_service(self, service):
        self._service = service

    def log(self, block_number: int, dataclass: str, message_type: str, message: str, exception_env={}, level="Info"):
        if self._service is not None:
            self._log_buffer.put(
                {
                    "block_number": block_number,
                    "dataclass": dataclass,
                    "message_type": message_type,
                    "message": message,
                    "exception_env": exception_env,
                    "level": level,
                }
            )
            self._check_and_flush()

    def force_to_flush(self):
        if self._service is not None:
            with self._queue_lock:
                with self._flush_lock:
                    # Double-check after acquiring flush lock
                    logs = []
                    while not self._log_buffer.empty():
                        logs.append(self._log_buffer.get())
                    self._flush_logs_to_db(logs)

    def _check_and_flush(self):
        if self._log_buffer.qsize() >= LOG_BUFFER_SIZE:
            with self._queue_lock:
                # Double-check after acquiring queue lock
                if self._log_buffer.qsize() >= LOG_BUFFER_SIZE:
                    with self._flush_lock:
                        logs = []
                        while not self._log_buffer.empty():
                            logs.append(self._log_buffer.get())
                        self._flush_logs_to_db(logs)

    def _flush_logs_to_db(self, logs):
        with self._service.session_scope() as session:
            try:
                statement = insert(ExceptionRecords).values(logs)
                session.execute(statement)
                session.commit()
            except Exception as e:
                print(e)
