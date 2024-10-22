import json
import os


abi_map = {}


fs = os.listdir("./")
for a_f in fs:
    if a_f.endswith(".json"):
        with open(a_f, "r") as data_file:
            dic = json.load(data_file)
            abi_map[dic["address"].lower()] = json.dumps(dic["abi"])
