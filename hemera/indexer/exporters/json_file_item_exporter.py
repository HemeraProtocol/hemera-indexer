import json
import logging
import os
from datetime import datetime
from typing import List

from dateutil.tz import tzlocal

from hemera.common.utils.file_utils import smart_open
from hemera.indexer.domains import Domain, dataclass_to_dict
from hemera.indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)

DEFAULT_BLOCKS_PER_FILE = int(os.environ.get("DEFAULT_BLOCKS_PER_FILE", "1000"))


class JSONFileItemExporter(BaseExporter):

    def __init__(self, direction, config):
        self.dir = direction.replace("jsonfile://", "")
        self.blocks_per_file = config.get("blocks_per_file", DEFAULT_BLOCKS_PER_FILE)

    def export_items(self, items: List[Domain], **kwargs):
        start_time = datetime.now(tzlocal())

        try:
            items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    self.split_items_to_file(item_type.type(), item_group)

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

    def split_items_to_file(self, item_type: str, items: List[Domain]):
        if hasattr(items[0], "number"):
            items.sort(key=lambda x: x.number)
        elif hasattr(items[0], "block_number"):
            items.sort(key=lambda x: x.block_number)

        first, last = items[0], items[-1]
        dict_items = [dataclass_to_dict(item) for item in items]
        if hasattr(first, "number"):
            block_range = (first.number, last.number)

            # append extra data which definitely out of range to trigger items writing
            dict_items.append({"number": last.number + self.blocks_per_file})
            dict_items.sort(key=lambda x: x["number"])
        elif hasattr(first, "block_number"):
            block_range = (first.block_number, last.block_number)

            # append extra data which definitely out of range to trigger items writing
            dict_items.append({"block_number": last.block_number + self.blocks_per_file})
            dict_items.sort(key=lambda x: x["block_number"])
        else:
            block_range = None

        if block_range:
            data_sink_ranges = self.calculate_file_range(block_range)

            range_index = 0
            file_items = []
            for item in dict_items:
                if (
                    "number" in item
                    and data_sink_ranges[range_index][0] <= item["number"] <= data_sink_ranges[range_index][1]
                ):
                    file_items.append(item)
                elif (
                    "block_number" in item
                    and data_sink_ranges[range_index][0] <= item["block_number"] <= data_sink_ranges[range_index][1]
                ):
                    file_items.append(item)
                else:
                    check_and_write(
                        os.path.join(
                            self.dir,
                            item_type,
                            f"{item_type}-{data_sink_ranges[range_index][0]}-{data_sink_ranges[range_index][1]}.json",
                        ),
                        file_items,
                    )
                    range_index += 1
                    file_items = [item]

        else:
            target_file_path = os.path.join(self.dir, item_type, f"{item_type}.json")
            check_and_write(target_file_path, dict_items[:-1])

    def calculate_file_range(self, block_range: tuple):
        range_begin, range_end = block_range
        if range_end - range_begin < self.blocks_per_file:
            return [block_range]

        file_begin = range_begin
        file_ranges = []
        while file_begin <= range_end:
            file_end = file_begin + self.blocks_per_file - 1
            file_ranges.append((file_begin, file_end))
            file_begin = file_end + 1

        return file_ranges


def check_and_write(file_path: str, items: List[dict]):
    if len(items) == 0:
        return

    with smart_open(file_path, mode="w") as file_handle:
        for item in items:
            file_handle.write(json.dumps(item) + "\n")
