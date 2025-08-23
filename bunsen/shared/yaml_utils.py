"""YAML utilities"""

import yaml


def load_yaml_file(file_path: str) -> dict:
    """Loads and parses a YAML file from a given path.

    Args:
        file_path (str): The full path to the YAML file.

    Returns:
        Dict: A dictionary containing the parsed YAML data.
              Returns an empty dictionary if the file is not found.
    """
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file not found at '{file_path}'.")
        return {}


def dump_yaml_file(file_path: str, data: dict):
    """Saves a dictionary to a YAML file at a given path.

    Args:
        file_path (str): The full path to the YAML file.
        data (dict): The dictionary to be saved as YAML.
    """
    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing to file '{file_path}': {e}")
