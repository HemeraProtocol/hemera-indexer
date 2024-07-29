import os
from datetime import timezone, datetime

from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import insert

from common.models.sync_record import SyncRecord
from common.utils.file_utils import write_to_file, smart_open


class BaseRecorder(object):
    def set_last_synced_block(self, last_synced_block):
        pass

    def get_last_synced_block(self):
        pass


class FileSyncRecorder(BaseRecorder):

    def __init__(self, file_name):
        self.file_name = file_name

    def set_last_synced_block(self, last_synced_block):
        write_to_file(self.file_name, str(last_synced_block) + '\n')

    def get_last_synced_block(self):
        if not os.path.isfile(self.file_name):
            self.set_last_synced_block(0)
            return 0
        with smart_open(self.file_name, 'r') as last_synced_block_file:
            return int(last_synced_block_file.read())


class PGSyncRecorder(BaseRecorder):

    def __init__(self, mission, key, service):
        self.mission = mission
        self.key = key
        self.service = service

    def set_last_synced_block(self, last_synced_block):
        session = self.service.get_service_session()
        update_time = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))
        try:
            statement = insert(SyncRecord).values({
                "mission_type": self.mission,
                "mission_sign": self.key,
                "last_block_number": last_synced_block,
                "update_time": update_time
            }).on_conflict_do_update(index_elements=[SyncRecord.mission_type, SyncRecord.mission_sign],
                                     set_=
                                     {
                                         "last_block_number": last_synced_block,
                                         "update_time": update_time
                                     })

            session.execute(statement)
            session.commit()
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

    def get_last_synced_block(self):
        session = self.service.get_service_session()
        try:
            result = session.query(SyncRecord.last_block_number).filter(
                and_(SyncRecord.mission_type == self.mission,
                     SyncRecord.mission_sign == self.key)
            ).scalar()
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()
        if result is not None:
            return result
        return 0


def create_recorder(mission: str, sync_recorder: str, config: dict) -> BaseRecorder:
    cut_begin = sync_recorder.find('_')
    if cut_begin == -1:
        raise ValueError(f'Invalid sync recorder: {sync_recorder}''')

    recorder = sync_recorder[cut_begin + 1:]

    if sync_recorder.startswith('pg'):
        try:
            service = config['db_service']
        except KeyError:
            raise ValueError(f'postgresql sync record must provide pg config.')
        return PGSyncRecorder(mission, recorder, service)

    elif sync_recorder.startswith('file'):
        return FileSyncRecorder(mission, recorder)

    else:
        raise ValueError('Unable to determine sync recorder type: ' + sync_recorder)
