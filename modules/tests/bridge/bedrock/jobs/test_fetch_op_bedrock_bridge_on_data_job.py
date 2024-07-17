import pytest

from common.services.postgresql_service import PostgreSQLService

from indexer.exporters.postgres_item_exporter import PostgresItemExporter
from modules.bridge.bedrock.extractor.l1_bridge_data_extractor import L1BridgeDataExtractor

from modules.bridge.bedrock.parser.function_parser import BedRockFunctionCallType
from modules.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN, \
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED, convert_bridge_items
from modules.jobs.fetch_filter_data_job import FetchFilterDataJob
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from indexer.utils.utils import  verify_db_connection_url


@pytest.mark.util
def test_fetch_op_bedrock_bridge_on_data():
    service_url = verify_db_connection_url("postgresql+psycopg2://postgres:password@localhost:5432/explorer_test")

    service = PostgreSQLService(service_url, db_version="base")

    op_bedrock_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log',
                    L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1,
                    L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN,
                    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED],
        export_keys=[L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN,
                     L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED],
        start_block=20273057,
        end_block=20273060,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=L1BridgeDataExtractor(
            optimism_portal_proxy="0x9168765ee952de7c6f8fc6fad5ec209b960b7622"
        ),
        item_exporter=PostgresItemExporter(service, convert_items=convert_bridge_items),
    )

    op_bedrock_job.run()
