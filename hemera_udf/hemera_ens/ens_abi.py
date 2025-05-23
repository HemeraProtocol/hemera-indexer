import json
import os


def load_abi_from_directory(relative_path):
    """
    Load ABI files from the specified relative directory and build an abi_map.

    :param relative_path: The relative path to the directory containing ABI files.
    :return: A dictionary mapping addresses (lowercased) to their ABI JSON strings.
    """
    abi_map = {}
    # Get the absolute path of the directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.join(current_dir, relative_path)

    # Iterate through all files in the directory
    for file_name in os.listdir(absolute_path):
        file_path = os.path.join(absolute_path, file_name)
        # Process only files, skip directories
        if os.path.isfile(file_path):
            with open(file_path, "r") as data_file:
                try:
                    data = json.load(data_file)
                    abi_map[data["address"].lower()] = json.dumps(data["abi"])
                except (KeyError, json.JSONDecodeError) as e:
                    print(f"Error processing file {file_name}: {e}")

    return abi_map


relative_path = "abi"
abi_map = load_abi_from_directory(relative_path)
