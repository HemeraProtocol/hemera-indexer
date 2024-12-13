import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from tests_commons import CYBER_PUBLIC_NODE_RPC_URL, LINEA_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_id_info_job_on_cyber():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail,
        ],
    )

    job_scheduler.run_jobs(
        start_block=4536864,
        end_block=4536864,
    )

    data_buff = job_scheduler.get_data_buff()

    erc1155_token_id_details = data_buff[ERC1155TokenIdDetail.type()]
    assert len(erc1155_token_id_details) == 1

    assert (
        ERC1155TokenIdDetail(
            token_address="0x2d9181b954736971bb74043d4782dfe93b55a9af",
            token_id=9,
            token_uri="https://metadata.cyberconnect.dev/nfts/ss-projects/9.json",
            block_number=4536864,
            block_timestamp=1722502295,
            token_uri_info=None,
        )
        in erc1155_token_id_details
    )

    update_erc1155_token_id_details = data_buff[UpdateERC1155TokenIdDetail.type()]
    assert len(update_erc1155_token_id_details) == 1
    assert (
        UpdateERC1155TokenIdDetail(
            token_address="0x2d9181b954736971bb74043d4782dfe93b55a9af",
            token_id=9,
            token_supply=31380,
            block_number=4536864,
            block_timestamp=1722502295,
        )
        in update_erc1155_token_id_details
    )

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_id_info_job_on_cyber_mul():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail,
        ],
        multicall=True,
    )

    job_scheduler.run_jobs(
        start_block=4536864,
        end_block=4536864,
    )

    data_buff = job_scheduler.get_data_buff()

    erc1155_token_id_details = data_buff[ERC1155TokenIdDetail.type()]
    assert len(erc1155_token_id_details) == 1

    assert (
        ERC1155TokenIdDetail(
            token_address="0x2d9181b954736971bb74043d4782dfe93b55a9af",
            token_id=9,
            token_uri="https://metadata.cyberconnect.dev/nfts/ss-projects/9.json",
            block_number=4536864,
            block_timestamp=1722502295,
            token_uri_info=None,
        )
        in erc1155_token_id_details
    )

    update_erc1155_token_id_details = data_buff[UpdateERC1155TokenIdDetail.type()]
    assert len(update_erc1155_token_id_details) == 1
    assert (
        UpdateERC1155TokenIdDetail(
            token_address="0x2d9181b954736971bb74043d4782dfe93b55a9af",
            token_id=9,
            token_supply=31380,
            block_number=4536864,
            block_timestamp=1722502295,
        )
        in update_erc1155_token_id_details
    )

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_id_info_job_on_linea():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                LINEA_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                LINEA_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=10,
        debug_batch_size=1,
        max_workers=1,
        config={},
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail,
        ],
    )

    job_scheduler.run_jobs(
        start_block=8494071,
        end_block=8494071,
    )

    data_buff = job_scheduler.get_data_buff()

    erc721_token_id_changes = data_buff[ERC721TokenIdChange.type()]
    assert len(erc721_token_id_changes) == 1
    assert (
        ERC721TokenIdChange(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_owner="0xa53cca02f98d590819141aa85c891e2af713c223",
            block_number=8494071,
            block_timestamp=1724397109,
        )
        in erc721_token_id_changes
    )

    erc721_token_id_details = data_buff[ERC721TokenIdDetail.type()]
    assert len(erc721_token_id_details) == 1
    assert (
        ERC721TokenIdDetail(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_uri="",
            block_number=8494071,
            block_timestamp=1724397109,
            token_uri_info=None,
        )
        in erc721_token_id_details
    )

    update_erc721_token_id_details = data_buff[UpdateERC721TokenIdDetail.type()]
    assert len(update_erc721_token_id_details) == 1
    assert (
        UpdateERC721TokenIdDetail(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_owner="0xa53cca02f98d590819141aa85c891e2af713c223",
            block_number=8494071,
            block_timestamp=1724397109,
        )
        in update_erc721_token_id_details
    )

    erc1155_token_id_details = data_buff[ERC1155TokenIdDetail.type()]
    assert len(erc1155_token_id_details) == 1
    assert (
        ERC1155TokenIdDetail(
            token_address="0xa53cca02f98d590819141aa85c891e2af713c223",
            token_id=54780668040604116915679158082040366453838453357839560563054770201457212183923,
            token_uri="ens-metadata-service.appspot.com/name/0x{id}",
            block_number=8494071,
            block_timestamp=1724397109,
            token_uri_info=None,
        )
        in erc1155_token_id_details
    )

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_id_info_job_on_linea_mul():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                LINEA_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                LINEA_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=10,
        debug_batch_size=1,
        max_workers=1,
        config={},
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail,
        ],
        multicall=True,
    )

    job_scheduler.run_jobs(
        start_block=8494071,
        end_block=8494071,
    )

    data_buff = job_scheduler.get_data_buff()

    erc721_token_id_changes = data_buff[ERC721TokenIdChange.type()]
    assert len(erc721_token_id_changes) == 1
    assert (
        ERC721TokenIdChange(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_owner="0xa53cca02f98d590819141aa85c891e2af713c223",
            block_number=8494071,
            block_timestamp=1724397109,
        )
        in erc721_token_id_changes
    )

    erc721_token_id_details = data_buff[ERC721TokenIdDetail.type()]
    assert len(erc721_token_id_details) == 1
    assert (
        ERC721TokenIdDetail(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_uri="",
            block_number=8494071,
            block_timestamp=1724397109,
            token_uri_info=None,
        )
        in erc721_token_id_details
    )

    update_erc721_token_id_details = data_buff[UpdateERC721TokenIdDetail.type()]
    assert len(update_erc721_token_id_details) == 1
    assert (
        UpdateERC721TokenIdDetail(
            token_address="0x6e84390dcc5195414ec91a8c56a5c91021b95704",
            token_id=110042221770367602542853534930234725702383442308140339620523913150618217206456,
            token_owner="0xa53cca02f98d590819141aa85c891e2af713c223",
            block_number=8494071,
            block_timestamp=1724397109,
        )
        in update_erc721_token_id_details
    )

    erc1155_token_id_details = data_buff[ERC1155TokenIdDetail.type()]
    assert len(erc1155_token_id_details) == 1
    assert (
        ERC1155TokenIdDetail(
            token_address="0xa53cca02f98d590819141aa85c891e2af713c223",
            token_id=54780668040604116915679158082040366453838453357839560563054770201457212183923,
            token_uri="ens-metadata-service.appspot.com/name/0x{id}",
            block_number=8494071,
            block_timestamp=1724397109,
            token_uri_info=None,
        )
        in erc1155_token_id_details
    )

    job_scheduler.clear_data_buff()
