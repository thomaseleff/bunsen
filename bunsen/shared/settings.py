"""Environment and settings"""

import dotenv
from pathlib import Path
import os

from bunsen.shared import yaml_utils

# Default settings location
DEFAULT_SETTINGS_PATH = Path(Path.cwd(), ".bunsen", "settings.yaml")
DEFAULT_ISSUE_AGENT_SETTINGS_PATH = Path(Path.cwd(), ".bunsen", "issue_agent.yaml")
DEFAULT_SWE_AGENT_SETTINGS_PATH = Path(Path.cwd(), ".bunsen", "swe_agent.yaml")

# Default model settings
DEFAULT_ISSUE_AGENT_SETTINGS = {  # This `.yaml` config has limited settings
    "agent": {
        "templates": {
            "system_template": """
                You are an intelligent and friendly product / business analyst AI agent. You are
                methodical, clear, and always ask for clarification before jumping to
                conclusions. You do not use emojis.
            """
        }
    }
}
DEFAULT_SWE_AGENT_SETTINGS = {  # This `.yaml` config is defined by `swe-agent`
    "agent": {
        "templates": {
            "system_template": "You are a helpful assistant that can interact with a computer to solve tasks.",
            "instance_template": """
                <uploaded_files>
                {{working_dir}}
                </uploaded_files>
                I've uploaded a python code repository in the directory {{working_dir}}. Consider the following PR description:

                <pr_description>
                {{problem_statement}}
                </pr_description>

                Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
                I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!
                Your task is to make the minimal changes to non-tests files in the {{working_dir}} directory to ensure the <pr_description> is satisfied.
                Follow these steps to resolve the issue:
                1. As a first step, it might be a good idea to find and read code relevant to the <pr_description>
                2. Create a script to reproduce the error and execute it with `python <filename.py>` using the bash tool, to confirm the error
                3. Edit the sourcecode of the repo to resolve the issue
                4. Rerun your reproduce script and confirm that the error is fixed!
                5. Think about edgecases and make sure your fix handles them as well
                Your thinking should be thorough and so it's fine if it's very long.
            """,
            "next_step_template": """
                OBSERVATION:
                {{observation}}
            """,
            "next_step_no_output_template": "Your command ran successfully and did not produce any output."
        },
        "tools": {
            "env_variables": {
                "PAGER": "cat",
                "MANPAGER": "cat",
                "LESS": "-R",
                "PIP_PROGRESS_BAR": "off",
                "TQDM_DISABLE": "1",
                "GIT_PAGER": "cat"
            },
            "bundles": [
                {
                    "path": "tools/registry"
                },
                {
                    "path": "tools/edit_anthropic"
                },
                {
                    "path": "tools/review_on_submit_m"
                }
            ],
            "registry_variables": {
                "USE_FILEMAP": "true",
                "SUBMIT_REVIEW_MESSAGES": [
                    "Thank you for your work on this issue. Please carefully follow the steps below to help review your changes.\n\n1. If you made any changes to your code after running the reproduction script, please run the reproduction script again.\n  If the reproduction script is failing, please revisit your changes and make sure they are correct.\n  If you have already removed your reproduction script, please ignore this step.\n2. Remove your reproduction script (if you haven't done so already).\n3. If you have modified any TEST files, please revert them to the state they had before you started fixing the issue.\n  You can do this with `git checkout -- /path/to/test/file.py`. Use below <diff> to find the files you need to revert.\n4. Run the submit command again to confirm.\n\nHere is a list of all of your changes:\n\n<diff>\n{{diff}}\n</diff>\n"
                ]
            },
            "enable_bash_tool": True,
            "parse_function": {
                "type": "function_calling"
            }
        },
        "history_processors": [
            {
                "type": "cache_control",
                "last_n_messages": 2
            }
        ],
        "model": {
            "temperature": 1.0,
            "completion_kwargs": {
                "reasoning_effort": "high"
            }
        }
    }
}

if not DEFAULT_SETTINGS_PATH.exists():
    raise FileNotFoundError(
        f"The `settings.yaml` configuration file cannot be found at {DEFAULT_SETTINGS_PATH}."
    )

# Load environment
dotenv.load_dotenv()

# Load settings
SETTINGS = yaml_utils.load_yaml_file(DEFAULT_SETTINGS_PATH)

# Load model settings
if DEFAULT_ISSUE_AGENT_SETTINGS_PATH.exists():
    ISSUE_AGENT = yaml_utils.load_yaml_file(DEFAULT_ISSUE_AGENT_SETTINGS_PATH)
else:
    ISSUE_AGENT = DEFAULT_ISSUE_AGENT_SETTINGS.copy()

    # Create the `.yaml` configuration when it does not exist
    yaml_utils.dump_yaml_file(DEFAULT_ISSUE_AGENT_SETTINGS_PATH, DEFAULT_ISSUE_AGENT_SETTINGS)

if DEFAULT_SWE_AGENT_SETTINGS_PATH.exists():
    SWE_AGENT = yaml_utils.load_yaml_file(DEFAULT_SWE_AGENT_SETTINGS_PATH)
else:
    SWE_AGENT = DEFAULT_SWE_AGENT_SETTINGS.copy()

    # Create the `.yaml` configuration when it does not exist
    yaml_utils.dump_yaml_file(DEFAULT_SWE_AGENT_SETTINGS_PATH, DEFAULT_SWE_AGENT_SETTINGS)

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
