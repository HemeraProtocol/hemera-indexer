import os
import logging

import click

from indexer.exporters.item_exporter import check_exporter_in_chosen, ItemExporterType


def check_file_exporter_parameter(outputs, block_batch_size, blocks_per_file):
    if outputs is not None and \
            (check_exporter_in_chosen(outputs, ItemExporterType.CSVFILE) or
             check_exporter_in_chosen(outputs, ItemExporterType.JSONFILE)):
        if block_batch_size > blocks_per_file or block_batch_size % blocks_per_file != 0:
            raise click.ClickException("-B must be an integer multiple of --blocks-per-file."
                                       f"for now: -B is {block_batch_size}, --blocks-per-file is {blocks_per_file}")


def check_file_load_parameter(load_file_path):
    if not os.path.exists(load_file_path):
        raise click.ClickException("--source-path must be an existing file path.")

    for root, dirs, files in os.walk(load_file_path):
        for file in files:
            if file.endswith('csv') or file.endswith('json'):
                return

    logging.warning('Providing data path does not have any .csv or .json file. '
                    'The Following custom job will not have any data input. ')
