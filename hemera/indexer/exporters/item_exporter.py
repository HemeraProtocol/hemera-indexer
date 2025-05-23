from hemera.indexer.exporters.base_exporter import BaseExporter
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.exporters.csv_file_item_exporter import CSVFileItemExporter
from hemera.indexer.exporters.json_file_item_exporter import JSONFileItemExporter
from hemera.indexer.exporters.kafka_exporter import KafkaItemExporter
from hemera.indexer.exporters.postgres_item_exporter import PostgresItemExporter


def create_item_exporters(outputs, config):
    split_outputs = [output.strip() for output in outputs.split(",")] if outputs else []
    return [create_item_exporter(output, config) for output in split_outputs]


def create_item_exporter(output, config):
    item_exporter_type = determine_item_exporter_type(output)

    if item_exporter_type == ItemExporterType.CONSOLE:
        item_exporter = ConsoleItemExporter()
    elif item_exporter_type == ItemExporterType.POSTGRES:
        item_exporter = PostgresItemExporter(postgres_url=config["db_service"].jdbc_url)
    elif item_exporter_type == ItemExporterType.JSONFILE:
        item_exporter = JSONFileItemExporter(output, config)
    elif item_exporter_type == ItemExporterType.CSVFILE:
        item_exporter = CSVFileItemExporter(output, config)
    elif item_exporter_type == ItemExporterType.KAFKA:
        item_exporter = KafkaItemExporter(output)
    # TODO: Implement HemeraAddressPostgresItemExporter dynamically importing it
    # elif item_exporter_type == ItemExporterType.HEMERA_ADDRESS_POSTGRES:
    #     item_exporter = HemeraAddressPostgresItemExporter(output, config["chain_id"])
    elif item_exporter_type == ItemExporterType.VOID:
        item_exporter = BaseExporter()
    else:
        raise ValueError("Unable to determine item exporter type for output " + output)

    return item_exporter


def get_bucket_and_path_from_gcs_output(output):
    output = output.replace("gs://", "")
    bucket_and_path = output.split("/", 1)
    bucket = bucket_and_path[0]
    if len(bucket_and_path) > 1:
        path = bucket_and_path[1]
    else:
        path = ""
    return bucket, path


def determine_item_exporter_type(output):
    if output is not None and output == "postgres":
        return ItemExporterType.POSTGRES
    if output is not None and output.startswith("hemera_postgresql://"):
        return ItemExporterType.HEMERA_ADDRESS_POSTGRES
    elif output is not None and output.startswith("jsonfile://"):
        return ItemExporterType.JSONFILE
    elif output is not None and output.startswith("csvfile://"):
        return ItemExporterType.CSVFILE
    elif output is not None and output.startswith("kafka://"):
        return ItemExporterType.KAFKA
    elif output is not None and output == "void":
        return ItemExporterType.VOID
    elif output is None or output == "console":
        return ItemExporterType.CONSOLE

    else:
        return ItemExporterType.UNKNOWN


class ItemExporterType:
    VOID = "void"
    POSTGRES = "postgres"
    JSONFILE = "jsonfile"
    CSVFILE = "csvfile"
    CONSOLE = "console"
    UNKNOWN = "unknown"
    KAFKA = "kafka"
    HEMERA_ADDRESS_POSTGRES = "hemera_address_postgres"


def check_exporter_in_chosen(outputs, exporter_type: str):
    for output in outputs.split(","):
        if determine_item_exporter_type(output) == exporter_type:
            return True

    return False
