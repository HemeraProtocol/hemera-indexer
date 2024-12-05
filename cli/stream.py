import click

from cli.commands.log import log_setting
from cli.commands.performance import block_step, delay_control, multi_performance, single_performance
from cli.commands.progress import index_range, index_record
from cli.commands.rpc import rpc_provider
from cli.commands.schedule import filter_mode, job_config, job_schedule, reorg_switch
from cli.commands.source import source_control
from cli.commands.storage import cache_target, file_size, pid_file_storage, postgres, postgres_initial, sink_target
from cli.core.stream_process import stream_process


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
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
def stream(
    provider_uri=None,
    debug_provider_uri=None,
    entity_types=None,
    output_types=None,
    force_filter_mode=False,
    auto_reorg=False,
    config_file=None,
    source_path=None,
    source_types=None,
    output=None,
    blocks_per_file=None,
    cache="memory",
    postgres_url=None,
    db_version=None,
    init_schema=False,
    start_block=None,
    end_block=None,
    sync_recorder="file:sync_record",
    retry_from_record=False,
    block_batch_size=1,
    batch_size=10,
    debug_batch_size=1,
    max_workers=5,
    multicall=True,
    process_numbers=1,
    process_size=None,
    process_time_out=None,
    period_seconds=10,
    delay=0,
    log_file=None,
    log_level="INFO",
    pid_file=None,
):
    stream_process(
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
    )
