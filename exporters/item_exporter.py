from exporters.console_item_exporter import ConsoleItemExporter
from exporters.local_file_item_exporter import LocalFileItemExporter
from exporters.multi_item_exporter import MultiItemExporter
from exporters.postgres_item_exporter import PostgresItemExporter


def create_item_exporters(outputs, config):
    split_outputs = [output.strip() for output in outputs.split(',')] if outputs else ['console']

    item_exporters = [create_item_exporter(output, config) for output in split_outputs]
    return MultiItemExporter(item_exporters)


def create_item_exporter(output, config):
    item_exporter_type = determine_item_exporter_type(output)

    if item_exporter_type == ItemExporterType.CONSOLE:
        item_exporter = ConsoleItemExporter()

    elif item_exporter_type == ItemExporterType.POSTGRES:
        item_exporter = PostgresItemExporter(output, config)

    elif item_exporter_type == ItemExporterType.LOCALFILESYS:
        item_exporter = LocalFileItemExporter(output, config)

    else:
        raise ValueError('Unable to determine item exporter type for output ' + output)

    return item_exporter


def get_bucket_and_path_from_gcs_output(output):
    output = output.replace('gs://', '')
    bucket_and_path = output.split('/', 1)
    bucket = bucket_and_path[0]
    if len(bucket_and_path) > 1:
        path = bucket_and_path[1]
    else:
        path = ''
    return bucket, path


def determine_item_exporter_type(output):
    if output is not None and output.startswith('postgresql'):
        return ItemExporterType.POSTGRES
    elif output is not None and output.startswith('file://'):
        return ItemExporterType.LOCALFILESYS
    elif output is None or output == 'console':
        return ItemExporterType.CONSOLE
    else:
        return ItemExporterType.UNKNOWN


class ItemExporterType:
    POSTGRES = 'postgres'
    LOCALFILESYS = 'file'
    CONSOLE = 'console'
    UNKNOWN = 'unknown'
