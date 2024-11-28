import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from glob import glob
from typing import List

from dateutil.tz import tzlocal

from common.utils.file_utils import scan_tmp_files, smart_delete, smart_open
from indexer.domains import Domain, dataclass_to_dict
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)


class JSONFileItemExporter(BaseExporter):

    def __init__(self, direction, config):
        partition_size = config.get("partition_size") if config.get("partition_size") else 50000

        self.dir = direction.replace("jsonfile://", "")
        self.partition_size = partition_size

    def export_items(self, items: List[Domain], **kwargs):
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
            "Exporting items to Json file end, Item count: {}, Took {}".format(len(items), (end_time - start_time))
        )

    def batch_finish(self):
        self.merge_tmp_files()

    def write_items_to_tmp_file(self, item_type: str, items: List[Domain]):
        first, last = items[0], items[-1]
        if hasattr(first, "timestamp"):
            time_range = f"{first.timestamp}_{last.timestamp}"
        elif hasattr(first, "block_timestamp"):
            time_range = f"{first.block_timestamp}_{last.block_timestamp}"
        else:
            time_range = None

        if time_range is not None:
            basic_file_path = f"{self.dir}/{item_type}/{item_type}-{time_range}"
        else:
            basic_file_path = f"{self.dir}/{item_type}/{item_type}"

        # delete unfinished tmp file because of except exit
        smart_delete(f"{self.dir}/{item_type}/*.tmp")

        tmp_file_name = basic_file_path + ".json.tmp"
        with smart_open(tmp_file_name, mode="w") as file_handle:
            for item in items:
                file_handle.write(json.dumps(dataclass_to_dict(item)) + "\n")

    def merge_tmp_files(self):
        tmp_files = scan_tmp_files(self.dir)
        for tmp_file in tmp_files:
            path_component = tmp_file.split("/")
            model = path_component[-2]

            data_to_file = dict()
            with smart_open(tmp_file, mode="r") as file_handle:
                for line in file_handle:
                    data = json.loads(line)

                    # build file name to write
                    if "timestamp" in data:
                        timestamp = data["timestamp"]
                    elif "block_timestamp" in data:
                        timestamp = data["block_timestamp"]
                    else:
                        timestamp = None

                    if timestamp is not None:
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        time_range = dt.strftime("%Y-%m-%d_%H:00:00")
                        exist_files = glob(f"{self.dir}/{model}/{model}-{time_range}*")
                        if len(exist_files) > 1:
                            to_file = f"{self.dir}/{model}/{model}-{time_range}_{len(exist_files) - 1}.json"
                        else:
                            to_file = f"{self.dir}/{model}/{model}-{time_range}.json"
                    else:
                        file_cnt = os.listdir("/".join(path_component[:-1]))
                        if len(file_cnt) > 1:
                            to_file = f"{self.dir}/{model}/{model}_{len(file_cnt) - 1}.json"
                        else:
                            to_file = f"{self.dir}/{model}/{model}.json"

                    if to_file not in data_to_file:
                        data_to_file[to_file] = [data]
                    else:
                        data_to_file[to_file].append(data)

            for to_file in data_to_file.keys():
                with smart_open(to_file, mode="a") as json_writer:
                    for data in data_to_file[to_file]:
                        json_writer.write(json.dumps(data) + "\n")

            smart_delete(tmp_file)
            # self.check_and_split_files(data_to_file.keys())

    def check_and_split_files(self, files):
        for file in files:
            if self.check_file_lines(file):
                self.split_file(file)

    def check_file_lines(self, file):
        out = subprocess.getoutput("wc -l %s" % file)
        return int(out.split()[0]) > self.partition_size

    def split_file(self, file):
        basic_file_path = file[:-5]
        with smart_open(file, "r") as file_handle:
            total = [json.loads((line.strip())) for line in file_handle.readlines()]

            sub_file_handlers = [
                open(f"{basic_file_path}_{i}.json", "w") for i in range(0, int(len(total) / self.partition_size) + 1)
            ]

            for i, data in enumerate(total):
                sub_file_handlers[int(i / self.partition_size)].write(json.dumps(data) + "\n")

            for sub_file in sub_file_handlers:
                sub_file.close()

        smart_delete(file)
