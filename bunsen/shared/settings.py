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
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_REPO_URL = SETTINGS.get("github", {}).get("repo_url")
GITHUB_MAIN_BRANCH = SETTINGS.get("github", {}).get("main_branch")
GITHUB_CODING_TRIGGER_LABEL = SETTINGS.get("github", {}).get("coding_trigger_label")
GITHUB_CODING_WORKFLOW_FILENAME = SETTINGS.get("github", {}).get("coding_workflow_filename")

BUNSEN_MODEL_NAME = SETTINGS.get("llm", {}).get("bunsen_model_name")
BEAKER_MODEL_NAME = SETTINGS.get("llm", {}).get("beaker_model_name")

if not all(
    [
        GITHUB_APP_ID,
        GITHUB_PRIVATE_KEY,
        GITHUB_WEBHOOK_SECRET,
        GITHUB_REPO_URL,
        GITHUB_MAIN_BRANCH,
        GITHUB_CODING_TRIGGER_LABEL,
        BUNSEN_MODEL_NAME,
        BEAKER_MODEL_NAME,
        GITHUB_CODING_WORKFLOW_FILENAME
    ]
):
    raise EnvironmentError(
        "Missing one or more required environment variables"
        " or settings from `settings.yaml`."
    )
