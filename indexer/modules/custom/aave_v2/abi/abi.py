import json
import os


def get_absolute_path(relative_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(current_dir, relative_path)
    return absolute_path


abi_map = {}

relative_path = "./"
absolute_path = get_absolute_path(relative_path)
fs = os.listdir(absolute_path)
for a_f in fs:
    if a_f.endswith(".json"):

        with open(os.path.join(absolute_path, a_f), "r") as data_file:
            dic = json.load(data_file)
            abi_map[dic["address"].lower()] = json.dumps(dic["abi"])
