import json
import logging
import collections
from datetime import datetime

from dateutil.tz import tzlocal

from utils.file_utils import write_to_file, smart_delete, smart_compress_file

logger = logging.getLogger(__name__)


class LocalFileItemExporter:

    def __init__(self, direction, config):
        partition_size = config.get('partition_size') if config.get('partition_size') else 10000
        time_range = config.get('time_range') if config.get('time_range') else ""

        self.dir = direction.replace("file://", "")
        self.partition_size = partition_size
        self.time_range = time_range

    def open(self):
        pass

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        try:
            items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    basic_file_path = f"{self.dir}/{item_type}/{item_type}-{self.time_range}"
                    smart_delete(basic_file_path + "*")

                    for i, item in enumerate(item_group):
                        if len(item_group) < self.partition_size:
                            file_name = basic_file_path + ".json"
                        else:
                            file_name = basic_file_path + f"-{int(i / self.partition_size)}.json"
                        copy_item = item.copy()
                        copy_item.pop("model")
                        write_to_file(file_name, json.dumps(copy_item) + "\n", 'a+')

                    smart_compress_file(f"{basic_file_path}*.json", "gzip -9")

        except Exception as e:
            print(e)
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            pass
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to Json file end, Item count: {}, Took {}".format(len(items), (end_time - start_time)))

    def export_item(self, item):
        print(json.dumps(item))

    def close(self):
        pass


def group_by_item_type(items):
    result = collections.defaultdict(list)
    for item in items:
        key = item["model"].__tablename__
        result[key].append(item)

    return result
