from datetime import datetime


def convert_str_ts(st):
    if not st:
        return None
    if isinstance(st, int):
        return datetime.fromtimestamp(st).strftime("%Y-%m-%d %H:%M:%S")
    if st:
        try:
            dt = datetime.strptime(st, "%Y-%m-%d %H:%M:%S %Z")
        except ValueError:
            try:
                dt = datetime.strptime(st, "%Y-%m-%d %H:%M:%S.%f %Z")
            except ValueError:
                return None
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None
