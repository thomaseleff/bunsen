import yaml
from typing import Dict


def load_yaml_file(file_path: str) -> Dict:
    """
    Loads and parses a YAML file from a given path.

    This utility function provides a reusable way to read configuration files
    safely and handles cases where the file might not exist.

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
