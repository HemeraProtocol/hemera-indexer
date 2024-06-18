import json
import logging
import collections
import os
import subprocess
from datetime import datetime, timezone

from dateutil.tz import tzlocal

from exporters.base_exporter import BaseExporter
from utils.file_utils import write_to_file, smart_delete, smart_compress_file, smart_open, scan_tmp_files

logger = logging.getLogger(__name__)


class JSONFileItemExporter(BaseExporter):

    def __init__(self, direction, config):
        partition_size = config.get('partition_size') if config.get('partition_size') else 50000

        self.dir = direction.replace("jsonfile://", "")
        self.partition_size = partition_size

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        try:
            items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    self.write_items_to_tmp_file(item_type, item_group)

        except Exception as e:
            print(e)
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            pass
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to Json file end, Item count: {}, Took {}".format(len(items), (end_time - start_time)))

    def batch_finish(self):
        self.merge_tmp_files()

    def write_items_to_tmp_file(self, item_type, items):
        first, last = items[0], items[-1]
        if 'timestamp' in first:
            time_range = f"{first['timestamp']}_{last['timestamp']}"
        elif 'block_timestamp' in first:
            time_range = f"{first['block_timestamp']}_{last['block_timestamp']}"
        else:
            time_range = None

        if time_range is not None:
            basic_file_path = f"{self.dir}/{item_type}/{item_type}-{time_range}"
        else:
            basic_file_path = f"{self.dir}/{item_type}/{item_type}"

        smart_delete(basic_file_path + ".json.tmp")
        with smart_open(basic_file_path + '.json.tmp', mode='a+') as file_handle:
            for item in items:
                copy_item = item.copy()
                copy_item['model'] = copy_item['model'].__name__
                file_handle.write(json.dumps(copy_item) + '\n')

    def merge_tmp_files(self):
        tmp_files = scan_tmp_files(self.dir)
        for tmp_file in tmp_files:
            path_component = tmp_file.split('/')
            model = path_component[-2]

            written_files = set()
            with smart_open(tmp_file, mode='r') as file_handle:
                for line in file_handle:
                    data = json.loads(line)

                    # build file name to write
                    if 'timestamp' in data:
                        timestamp = data['timestamp']
                    elif 'block_timestamp' in data:
                        timestamp = data['block_timestamp']
                    else:
                        timestamp = None

                    if timestamp is not None:
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        time_range = dt.strftime("%Y-%m-%d_%H:00:00")
                        to_file = f"{self.dir}/{model}/{model}-{time_range}.json"
                    else:
                        file_cnt = os.listdir('/'.join(path_component[:-1]))
                        if len(file_cnt) > 1:
                            to_file = f"{self.dir}/{model}/{model}_{len(file_cnt) - 1}.json"
                        else:
                            to_file = f"{self.dir}/{model}/{model}.json"
                    written_files.add(to_file)
                    write_to_file(to_file, json.dumps(data) + "\n", mode='a+')

            smart_delete(tmp_file)
            self.check_and_split_files(list(written_files))

    def check_and_split_files(self, files):
        for file in files:
            if self.check_file_lines(file):
                self.split_file(file)

    def check_file_lines(self, file):
        out = subprocess.getoutput("wc -l %s" % file)
        return int(out.split()[0]) > self.partition_size

    def split_file(self, file):
        basic_file_path = file[:-5]
        with smart_open(file, 'r') as file_handle:
            for line, data in enumerate(file_handle):
                write_to_file(f"{basic_file_path}({int(line / self.partition_size)}).json",
                              json.dumps(data) + "\n", mode='a+')


def group_by_item_type(items):
    result = collections.defaultdict(list)
    for item in items:
        key = item["model"].__tablename__
        result[key].append(item)

    return result
