import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from exporters.jdbc.schema.rpc_statistic import RPCStatistic

logger = logging.getLogger(__name__)


class RPCStatisticService(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.db_service = None
        self.rpc_endpoint = None
        self.debug_rpc_endpoint = None

    def init_service(self, service, rpc_endpoint, debug_rpc_endpoint):
        self.db_service = service
        self.rpc_endpoint = rpc_endpoint
        self.debug_rpc_endpoint = debug_rpc_endpoint

    def increase_rpc_count(self, method, caller, count, is_debug=False):
        if self.db_service is None or self.rpc_endpoint is None or self.debug_rpc_endpoint is None:
            logger.warning(f"RPC statistic service is not initialized, RPC statistic service will not work. "
                           f"method: {method}, caller: {caller}, count: {count}")
            return
        update_time = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))
        session = self.db_service.get_service_session()
        try:
            statement = insert(RPCStatistic).values({
                "rpc_endpoint": self.debug_rpc_endpoint if is_debug else self.rpc_endpoint,
                "call_method": method,
                "caller_name": caller,
                "statistic_count": count,
                "update_time": update_time
            }).on_conflict_do_update(
                index_elements=[RPCStatistic.rpc_endpoint, RPCStatistic.call_method, RPCStatistic.caller_name],
                set_=
                {
                    "statistic_count": RPCStatistic.statistic_count + count,
                    "update_time": update_time
                })

            session.execute(statement)
            session.commit()

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()


statistic_service = RPCStatisticService()
