import logging
import os
import time

import click
from web3 import Web3

from hemera.common.enumeration.entity_type import calculate_entity_value, generate_output_types
from hemera.common.logo import print_logo
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.module_loading import import_submodules
from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.controller.stream_controller import StreamController
from hemera.indexer.exporters.item_exporter import create_item_exporters
from hemera.indexer.utils.buffer_service import BufferService
from hemera.indexer.utils.limit_reader import create_limit_reader
from hemera.indexer.utils.logging_utils import configure_logging, configure_signals
from hemera.indexer.utils.parameter_utils import (
    check_file_exporter_parameter,
    check_source_load_parameter,
    generate_dataclass_type_list_from_parameter,
)
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.rpc_utils import pick_random_provider_uri
from hemera.indexer.utils.sync_recorder import create_recorder
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"function {func.__name__} time: {execution_time:.6f} s")
        return result

    return wrapper


@calculate_execution_time
def stream_process(
    provider_uri,
    debug_provider_uri,
    entity_types,
    output_types,
    force_filter_mode,
    auto_reorg,
    config_file,
    source_path,
    source_types,
    output,
    blocks_per_file,
    cache,
    postgres_url,
    db_version,
    init_schema,
    start_block,
    end_block,
    sync_recorder,
    retry_from_record,
    block_batch_size,
    batch_size,
    debug_batch_size,
    max_workers,
    multicall,
    process_numbers,
    process_size,
    process_time_out,
    period_seconds,
    delay,
    log_file,
    log_level,
    pid_file,
):
    print_logo()
    import_submodules("hemera_udf")
    configure_logging(log_level, log_file)
    configure_signals()
    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.getLogger("ROOT").info("Using provider " + provider_uri)
    logging.getLogger("ROOT").info("Using debug provider " + debug_provider_uri)

    # parameter logic checking
    if source_path:
        check_source_load_parameter(source_path, start_block, end_block, auto_reorg)
    check_file_exporter_parameter(output, block_batch_size, blocks_per_file)

    # build config
    config = {
        "blocks_per_file": blocks_per_file,
        "source_path": source_path,
        "chain_id": Web3(Web3.HTTPProvider(provider_uri)).eth.chain_id,
    }

    if postgres_url:
        service = PostgreSQLService(postgres_url, db_version=db_version, init_schema=init_schema)
        config["db_service"] = service
    else:
        logging.getLogger("ROOT").warning("No postgres url provided. Exception recorder will not be useful.")

    if config_file:
        file_based_config = {}
        if not os.path.exists(config_file):
            raise click.ClickException(f"Config file {config_file} not found")
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                import json

                file_based_config = json.load(f)
            elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
                import yaml

                file_based_config = yaml.safe_load(f)
            else:
                raise click.ClickException(f"Config file {config_file} is not supported)")

        if file_based_config.get("chain_id") != config["chain_id"]:
            raise click.ClickException(
                f"Config file {config_file} is not compatible with chain_id {config['chain_id']}"
            )
        else:
            logging.getLogger("ROOT").info(f"Loading config from file: {config_file}, chain_id: {config['chain_id']}")
            config.update(file_based_config)
    output_types_by_entity_type = []
    if entity_types is not None:
        entity_types = calculate_entity_value(entity_types)
        output_types_by_entity_type = list(set(generate_output_types(entity_types)))

    output_types = list(
        set(generate_dataclass_type_list_from_parameter(output_types, "output") + output_types_by_entity_type)
    )

    if source_path and source_path.startswith("postgresql://"):
        source_types = generate_dataclass_type_list_from_parameter(source_types, "source")

    sync_recorder = create_recorder(sync_recorder, config)
    buffer_service = BufferService(
        item_exporters=create_item_exporters(output, config),
        required_output_types=[output.type() for output in output_types],
        success_callback=sync_recorder.handle_success,
        exception_callback=sync_recorder.set_failure_record,
    )

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        buffer_service=buffer_service,
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        max_workers=max_workers,
        config=config,
        required_output_types=output_types,
        required_source_types=source_types,
        cache=cache,
        auto_reorg=auto_reorg,
        multicall=multicall,
        force_filter_mode=force_filter_mode,
    )

    if process_numbers is None:
        process_numbers = 1
    if process_size is None:
        process_size = int(block_batch_size / process_numbers)
    if process_time_out is None:
        process_time_out = 300 * process_size

    controller = StreamController(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=False)),
        job_scheduler=job_scheduler,
        sync_recorder=sync_recorder,
        limit_reader=create_limit_reader(
            source_path, ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=False))
        ),
        retry_from_record=retry_from_record,
        delay=delay,
        process_numbers=process_numbers,
        process_size=process_size,
        process_time_out=process_time_out,
    )

    controller.action(
        start_block=start_block,
        end_block=end_block,
        block_batch_size=block_batch_size,
        period_seconds=period_seconds,
        pid_file=pid_file,
    )

    buffer_service.shutdown()
