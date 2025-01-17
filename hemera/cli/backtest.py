import os

import click

from hemera.cli.core.stream_process import stream_process
from hemera.cli.options.log import log_setting
from hemera.cli.options.performance import block_step, delay_control, multi_performance, single_performance
from hemera.cli.options.progress import index_range, index_record
from hemera.cli.options.rpc import rpc_provider
from hemera.cli.options.schedule import filter_mode, job_config, job_schedule, metrics_config, reorg_switch
from hemera.cli.options.source import source_control
from hemera.cli.options.storage import (
    cache_target,
    file_size,
    pid_file_storage,
    postgres,
    postgres_initial,
    sink_target,
)
from hemera.indexer.utils.parameter_utils import default_if_none


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@metrics_config
@rpc_provider
@job_schedule
@filter_mode
@reorg_switch
@job_config
@source_control
@sink_target
@file_size
@cache_target
@postgres
@postgres_initial
@index_range
@index_record
@block_step
@single_performance
@multi_performance
@delay_control
@log_setting
@pid_file_storage
def backtest(
    instance_name,
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
    persistence_type,
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
    os.environ["JOB_RETRIES"] = "1"

    block_batch_size = default_if_none(block_batch_size, 1)
    batch_size = default_if_none(batch_size, 1)
    debug_batch_size = default_if_none(debug_batch_size, 1)
    multicall = default_if_none(multicall, False)

    process_numbers = default_if_none(process_numbers, 1)

    period_seconds = default_if_none(period_seconds, 10)
    delay = default_if_none(delay, 0)

    retry_from_record = default_if_none(retry_from_record, False)

    stream_process(
        instance_name,
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
        persistence_type,
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
    )
