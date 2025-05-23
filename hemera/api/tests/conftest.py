import pytest

from hemera.api.app.config import *
from hemera.common.utils.config import set_config


@pytest.fixture(scope="module")
def test_client():
    app_config = AppConfig(
        api_modules=[
            APIModule.EXPLORER,
        ],
        env="ut",
        chain="test",
        contract_service="",
        db_read_sql_alchemy_database_config=DatabaseConfig(
            host="localhost",
            port=5432,
            database="indexer_test",
            username="postgres",
            password="admin",
        ),
        db_write_sql_alchemy_database_config=DatabaseConfig(
            host="localhost",
            port=5432,
            database="indexer_test",
            username="postgres",
            password="admin",
        ),
        db_common_sql_alchemy_database_config=DatabaseConfig(
            host="localhost",
            port=5432,
            database="indexer_test",
            username="postgres",
            password="admin",
        ),
        rpc="https://story-network.rpc.caldera.xyz/http",
    )
    set_config(app_config)
    from hemera.api.app.main import app

    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client
