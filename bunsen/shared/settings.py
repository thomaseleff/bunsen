"""Environment and settings"""

import dotenv
from pathlib import Path
import os

from bunsen.shared import yaml_utils

# Default settings location
DEFAULT_SETTINGS_PATH = Path(Path.cwd(), ".bunsen", "settings.yaml")

if not DEFAULT_SETTINGS_PATH.exists():
    raise FileNotFoundError(
        f"The `settings.yaml` configuration file cannot be found at {DEFAULT_SETTINGS_PATH}."
    )

# Load environment
dotenv.load_dotenv()

# Load settings
SETTINGS = yaml_utils.load_yaml_file(DEFAULT_SETTINGS_PATH)

# Constants
GITHUB_APP_ID = os.getenv("BUNSEN_GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("BUNSEN_GITHUB_PRIVATE_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("BUNSEN_GITHUB_WEBHOOK_SECRET")
GITHUB_REPO_URL = SETTINGS.get("github", {}).get("repo_url")
GITHUB_MAIN_BRANCH = SETTINGS.get("github", {}).get("main_branch")
GITHUB_CODING_TRIGGER_LABEL = SETTINGS.get("github", {}).get("coding_trigger_label")
GITHUB_CODING_WORKFLOW_FILENAME = SETTINGS.get("github", {}).get("coding_workflow_filename")

BUNSEN_MODEL_NAME = SETTINGS.get("llm", {}).get("bunsen_model_name")
BEAKER_MODEL_NAME = SETTINGS.get("llm", {}).get("beaker_model_name")

# Construct a dictionary of constants
_constants = {
    "env > BUNSEN_GITHUB_APP_ID": GITHUB_APP_ID,
    "env > BUNSEN_GITHUB_PRIVATE_KEY": GITHUB_PRIVATE_KEY,
    "env > BUNSEN_GITHUB_WEBHOOK_SECRET": GITHUB_WEBHOOK_SECRET,
    "settings > github > repo_url": GITHUB_REPO_URL,
    "settings > github > main_branch": GITHUB_MAIN_BRANCH,
    "settings > github > coding_trigger_label": GITHUB_CODING_TRIGGER_LABEL,
    "settings > github > coding_workflow_filename":  GITHUB_CODING_WORKFLOW_FILENAME,
    "llm > bunsen_model_name": BUNSEN_MODEL_NAME,
    "llm > beaker_model_name": BEAKER_MODEL_NAME,
}

# Identify missing constants
missing_constants = [
    constant for constant in _constants.keys() if not _constants.get(constant)
]

if missing_constants:
    raise EnvironmentError(
        "The following required environment variables"
        f" or settings from `settings.yaml` are missing: [{', '.join(missing_constants)}]."
    )
