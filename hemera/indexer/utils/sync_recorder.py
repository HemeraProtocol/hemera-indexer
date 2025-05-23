import json
import logging
import os
from datetime import datetime, timezone
from distutils.util import strtobool

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from hemera.common.models.failure_records import FailureRecords
from hemera.common.models.sync_record import SyncRecord
from hemera.common.utils.file_utils import smart_open, write_to_file

logger = logging.getLogger(__name__)

ASYNC_SUBMIT = bool(strtobool(os.environ.get("ASYNC_SUBMIT", "false")))


class BaseRecorder(object):

    def __init__(self, multi_mode: bool):
        self.multi_mode = multi_mode

    def set_last_synced_block(self, last_synced_block):
        pass

    def get_last_synced_block(self):
        pass

    def set_failure_record(self, output_types, start_block, end_block, exception_stage, exception):
        pass

    def handle_success(self, last_block_number):
        self.set_last_synced_block(last_block_number)
        logger.info("Writing last synced block {}".format(last_block_number))


class FileSyncRecorder(BaseRecorder):

    def __init__(self, file_name, multi_mode):
        super().__init__(multi_mode)
        self.file_name = file_name

    def set_last_synced_block(self, last_synced_block):
        if ASYNC_SUBMIT or self.multi_mode:
            wrote_synced_block = self.get_last_synced_block()
            if wrote_synced_block < last_synced_block:
                write_to_file(self.file_name, str(last_synced_block) + "\n")
        else:
            write_to_file(self.file_name, str(last_synced_block) + "\n")

    def get_last_synced_block(self):
        if not os.path.isfile(self.file_name):
            return 0
        with smart_open(self.file_name, "r") as last_synced_block_file:
            last_synced_block = last_synced_block_file.read()
            try:
                last_synced_block = int(last_synced_block)
            except ValueError as e:
                last_synced_block = 0
            return last_synced_block

    def set_failure_record(self, output_types, start_block, end_block, exception_stage, exception):
        failure_file = self.file_name + "_failure_records"
        crash_time = int(datetime.now(timezone.utc).timestamp())
        content = {
            "output_types": ",".join(output_types),
            "start_block_number": start_block,
            "end_block_number": end_block,
            "exception_stage": exception_stage,
            "exception": exception,
            "crash_time": crash_time,
        }

        write_to_file(failure_file, json.dumps(content) + "\n", "a+")


class PGSyncRecorder(BaseRecorder):

    def __init__(self, key, service, multi_mode):
        super().__init__(multi_mode)
        self.key = key
        self.service = service

    def set_last_synced_block(self, last_synced_block):
        session = self.service.get_service_session()
        update_time = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))
        try:
            conflict_args = {
                "index_elements": [SyncRecord.mission_sign],
                "set_": {
                    "last_block_number": last_synced_block,
                    "update_time": update_time,
                },
            }

            if ASYNC_SUBMIT or self.multi_mode:
                conflict_args["where"] = SyncRecord.last_block_number <= last_synced_block

            statement = (
                insert(SyncRecord)
                .values(
                    {
                        "mission_sign": self.key,
                        "last_block_number": last_synced_block,
                        "update_time": update_time,
                    }
                )
                .on_conflict_do_update(**conflict_args)
            )
            session.execute(statement)
            session.commit()
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_last_synced_block(self):
        session = self.service.get_service_session()
        try:
            result = session.query(SyncRecord.last_block_number).filter(SyncRecord.mission_sign == self.key).scalar()
        except Exception as e:
            raise e
        finally:
            session.close()
        if result is not None:
            return result
        return 0

    def set_failure_record(self, output_types, start_block, end_block, exception_stage, exception):
        session = self.service.get_service_session()
        try:
            crash_time = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))

            statement = insert(FailureRecords).values(
                {
                    "mission_sign": self.key,
                    "output_types": ",".join(output_types),
                    "start_block_number": start_block,
                    "end_block_number": end_block,
                    "exception_stage": exception_stage,
                    "exception": exception,
                    "crash_time": crash_time,
                }
            )

            session.execute(statement)
            session.commit()

        except Exception as e:
            raise e

        finally:
            session.close()


def create_recorder(sync_recorder: str, config: dict, multi_mode: bool) -> BaseRecorder:
    recorder_sign = sync_recorder.find(":")
    if recorder_sign == -1:
        raise ValueError(f"Invalid sync recorder: {sync_recorder}" "")

    recorder = sync_recorder.split(":")

    if recorder[0] == "pg":
        try:
            service = config["db_service"]
        except KeyError:
            raise ValueError(f"postgresql sync record must provide pg config.")
        return PGSyncRecorder(recorder[1], service, multi_mode)

    elif recorder[0] == "file":
        return FileSyncRecorder(recorder[1], multi_mode)

    else:
        raise ValueError("Unable to determine sync recorder type: " + sync_recorder)
