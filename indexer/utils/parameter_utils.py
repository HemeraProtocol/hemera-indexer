import logging
import os
import re

import click

from common.utils.format_utils import to_snake_case
from indexer.domain import Domain
from indexer.exporters.item_exporter import ItemExporterType, check_exporter_in_chosen
from indexer.utils.report_to_contract import RecordReporter


def extract_path_from_parameter(cli_path: str) -> str:
    substrings_to_remove = ["csvfile://", "jsonfile://"]
    pattern = "|".join(re.escape(sub) for sub in substrings_to_remove)
    file_path = re.sub(pattern, "", cli_path)

    return file_path


def check_file_exporter_parameter(outputs, block_batch_size, blocks_per_file):
    if outputs is not None and (
            check_exporter_in_chosen(outputs, ItemExporterType.CSVFILE)
            or check_exporter_in_chosen(outputs, ItemExporterType.JSONFILE)
    ):
        if block_batch_size > blocks_per_file or block_batch_size % blocks_per_file != 0:
            raise click.ClickException(
                "-B must be an integer multiple of --blocks-per-file."
                f"for now: -B is {block_batch_size}, --blocks-per-file is {blocks_per_file}"
            )


def check_source_load_parameter(cli_path: str, start_block=None, end_block=None, auto_reorg=False):
    if auto_reorg:
        raise click.ClickException(
            "Combine with read from source, --auto-reorg should keep its default value of false."
            "If you worried about data correctness with reorg, you could set --delay for indexing confirmed blocks"
        )

    if cli_path.startswith("postgresql://"):
        return

    if start_block is not None or end_block is not None:
        raise click.ClickException(
            "--source-path specify a file source. "
            "Combine with file source, --start-block and --end-block should be given."
        )

    load_file_path = extract_path_from_parameter(cli_path)

    if not os.path.exists(load_file_path):
        raise click.ClickException(f"--source-path must be an existing file path. provide path:{load_file_path}")

    for root, dirs, files in os.walk(load_file_path):
        for file in files:
            if file.endswith("csv") or file.endswith("json"):
                return

    logging.warning(
        "Providing data path does not have any .csv or .json file. "
        "The Following custom job will not have any data input. "
    )


def generate_dataclass_type_list_from_parameter(require_types: str, generate_type: str):
    domain_dict = Domain.get_all_domain_dict()
    parse_output_types = set()

    for output_type in require_types.split(","):
        output_type = to_snake_case(output_type)
        if output_type not in domain_dict:
            raise click.ClickException(f"{generate_type} type {output_type} is not supported")
        parse_output_types.add(domain_dict[output_type])

    if not require_types:
        raise click.ClickException(f"No {generate_type} types provided")
    types = list(set(parse_output_types))

    return types


def create_record_report_from_parameter(private_key, from_address, service):
    if private_key is None or from_address is None or service is None:
        logging.warning(
            "RecordReporter would not initialized, indexed records will not be reported to contract. "
            "The possible reason is that -pg or --report-private-key or --report-from-address are not set."
        )
        return None

    return RecordReporter(private_key, from_address, service)
