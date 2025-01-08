from typing import List, Union


def chunk_list(lst, chunk_size):
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def distinct_collections_by_group(collections: List[object], group_by: List[str], max_key: Union[str, None] = None):
    distinct = {}
    for item in collections:
        key = tuple(getattr(item, idx) for idx in group_by)

        if key not in distinct:
            distinct[key] = item
        else:
            if max_key is not None and getattr(distinct[key], max_key) < getattr(item, max_key):
                distinct[key] = item

    return [distinct[key] for key in distinct.keys()]


def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def merge_sort(sorted_col_a, sorted_col_b):
    merged = []
    a_index, a_len = 0, len(sorted_col_a)
    b_index, b_len = 0, len(sorted_col_b)

    while a_index < a_len and b_index < b_len:
        if sorted_col_a[a_index]["id"] < sorted_col_b[b_index]["id"]:
            merged.append(sorted_col_a[a_index])
            a_index += 1
        else:
            merged.append(sorted_col_b[b_index])
            b_index += 1

    merged.extend(sorted_col_a[a_index:])
    merged.extend(sorted_col_b[b_index:])

    return merged


def validate_range(range_start_incl, range_end_incl):
    if range_start_incl < 0 or range_end_incl < 0:
        raise ValueError("range_start and range_end must be greater or equal to 0")

    if range_end_incl < range_start_incl:
        raise ValueError("range_end must be greater or equal to range_start")


def split_to_batches(start_incl, end_incl, batch_size):
    """start_incl and end_incl are inclusive, the returned batch ranges are also inclusive"""
    for batch_start in range(start_incl, end_incl + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_incl)
        yield batch_start, batch_end


def merge_dataclasses(self, data_class, attributes):
    """sort dataclass by block_number, then keep the newest data"""
    if data_class.type() not in self._data_buff:
        return
    tmps = self._data_buff.pop(data_class.type())
    tmps.sort(key=lambda x: x.block_number, reverse=True)
    lis = []
    unique_k_set = set()
    for li in tmps:
        k = tuple([getattr(li, at) for at in attributes])
        if k not in unique_k_set:
            unique_k_set.add(k)
            lis.append(li)
    if len(lis) > 0:
        self._collect_items(data_class.type(), lis)
