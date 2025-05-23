import contextlib
import os
import pathlib
import subprocess
import sys
from glob import glob


# https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
@contextlib.contextmanager
def smart_open(filename=None, mode="w", binary=False, create_parent_dirs=True):
    fh = get_file_handle(filename, mode, binary, create_parent_dirs)

    try:
        yield fh
    finally:
        fh.close()


def smart_delete(path_format):
    file_list = glob(path_format)

    for file in file_list:
        delete_file(file)


def get_file_handle(filename, mode="w", binary=False, create_parent_dirs=True):
    if create_parent_dirs and filename is not None:
        dirname = os.path.dirname(filename)
        pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
    full_mode = mode + ("b" if binary else "")
    is_file = filename and filename != "-"
    if is_file:
        fh = open(filename, full_mode)
    elif filename == "-":
        fd = sys.stdout.fileno() if mode == "w" else sys.stdin.fileno()
        fh = os.fdopen(fd, full_mode)
    else:
        fh = NoopFile()
    return fh


def close_silently(file_handle):
    if file_handle is None:
        pass
    try:
        file_handle.close()
    except OSError:
        pass


def smart_compress_file(file_wildcards, compress_cmd):
    file_list = glob(file_wildcards)

    for file in file_list:
        subprocess.run(f"{compress_cmd} {file}", shell=True, check=True)


def init_last_block_file(start_block, last_block_file):
    write_last_block(last_block_file, start_block)


def read_last_block(file):
    with smart_open(file, "r") as last_synced_block_file:
        return int(last_synced_block_file.read())


def write_last_block(file, last_synced_block):
    write_to_file(file, str(last_synced_block) + "\n")


def write_to_file(file, content, mode="w"):
    with smart_open(file, mode) as file_handle:
        file_handle.write(content)


def scan_tmp_files(data_dir):
    paths = os.walk(data_dir)
    tmp_files = []

    for path, dirs, files in paths:
        for file in files:
            file_path = os.path.join(path, file)
            if file_path[-3:] == "tmp":
                tmp_files.append(file_path)

    return tmp_files


def delete_file(file):
    try:
        os.remove(file)
    except OSError:
        raise OSError


def get_project_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    return project_root


class NoopFile:
    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def readable(self):
        pass

    def writable(self):
        pass

    def seekable(self):
        pass

    def close(self):
        pass

    def write(self, bytes):
        pass
