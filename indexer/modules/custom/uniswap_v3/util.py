import json
import os


def load_abi(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, filename)
    with open(full_path, 'r') as file:
        data = json.load(file)
    return data
