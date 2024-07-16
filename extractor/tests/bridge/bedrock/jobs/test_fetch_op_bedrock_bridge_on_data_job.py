import pytest

from extractor.bridge.bedrock.extractor.l1_bridge_data_extractor import L1BridgeDataExtractor

from extractor.bridge.bedrock.parser.function_parser import BedRockFunctionCallType
from extractor.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN, \
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED
from extractor.jobs.fetch_filter_data_job import FetchFilterDataJob
from utils.provider import get_provider_from_uri
from utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.util
def test_fetch_op_bedrock_bridge_on_data():
    op_bedrock_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log',
                    L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1,
                    L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN,
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
    )

    op_bedrock_job.run()
