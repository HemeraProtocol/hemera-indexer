from sqlalchemy import func

from common.models.blocks import Blocks
from common.services.postgresql_service import PostgreSQLService
from common.utils.exception_control import FastShutdownError
from common.utils.web3_utils import build_web3
from indexer.utils.thread_local_proxy import ThreadLocalProxy


class LimitReader(object):
    def get_current_block_number(self):
        pass


class RPCLimitReader(LimitReader):

    def __init__(self, **kwargs):
        self.rpc_uri = kwargs.get("rpc_uri")
        self.web3 = build_web3(self.rpc_uri)

    def get_current_block_number(self):
        return int(self.web3.eth.block_number)


class PGLimitReader(LimitReader):

    def __init__(self, **kwargs):
        self.postgres_uri = kwargs.get("postgres_uri")
        self.service = PostgreSQLService(jdbc_url=self.postgres_uri)

    def get_current_block_number(self):
        session = self.service.get_service_session()
        try:
            block_number = session.query(func.max(Blocks.number)).scalar()
        finally:
            session.close()

        return block_number


def create_limit_reader(postgres_uri: str, rpc_uri: ThreadLocalProxy) -> LimitReader:
    if postgres_uri and postgres_uri.startswith("postgresql://"):
        return PGLimitReader(postgres_uri=postgres_uri)
    elif rpc_uri is not None:
        return RPCLimitReader(rpc_uri=rpc_uri)
    else:
        raise FastShutdownError(
            f"Unable to create limit reader with parameter postgres_uri:{postgres_uri} and rpc_uri:{rpc_uri}"
        )
