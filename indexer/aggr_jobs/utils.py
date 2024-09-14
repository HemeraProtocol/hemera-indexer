from datetime import datetime, timedelta

import click
from web3 import Web3

from common.models.sync_record import SyncRecord


def get_yesterday_date():
    now = datetime.now()

    yesterday_datetime = now - timedelta(days=1)

    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = yesterday_datetime.strftime("%Y-%m-%d")

    return yesterday_str, today_str


class DateType(click.ParamType):
    name = "date"

    def convert(self, value, param, ctx):
        try:
            if value is not None:
                datetime.strptime(value, "%Y-%m-%d")
                return value
        except ValueError:
            self.fail(f"{value} is not a valid date in YYYY-MM-DD format", param, ctx)


def check_data_completeness(db_service, provider_uri, end_date):
    record = read_sync_record(db_service)
    if not record:
        raise click.ClickException("There is something wrong with the sync record")
    web_ = Web3(Web3.HTTPProvider(provider_uri))
    task_end_ts = convert_date_to_timestramp(end_date)
    block = web_.eth.get_block(record)
    block_timestamp = block.timestamp
    if block_timestamp < task_end_ts:
        dt_object = datetime.fromtimestamp(block_timestamp)
        raise click.ClickException(
            f"Incomplete data detected. The latest available data is from {dt_object}, but the provided end_date is {end_date}."
        )


def convert_date_to_timestramp(date_string):
    dt_object = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt_object.timestamp())


def read_sync_record_from_file():
    try:
        with open("sync_record", "r") as file:
            sync_record = file.read().strip()
            return int(sync_record)
    except FileNotFoundError:
        print("sync_record file not found.")
        return None
    except ValueError:
        print("sync_record does not contain a valid number.")
        return None


def read_sync_record_from_pg(db_service):
    try:
        session = db_service.Session()
        latest_record = session.query(SyncRecord).first()
        record = latest_record.last_block_number
        return record
    except Exception:
        return None


def read_sync_record(db_service) -> int:
    record = read_sync_record_from_file()
    if not record:
        record = read_sync_record_from_pg(db_service)
    return record

def parse_job_list(job_name, configure_file):
    pass
