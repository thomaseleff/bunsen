import github
from bunsen.shared import yaml_utils


# This module defines the personas for the agents, including their GitHub identity.
# By centralizing this information, we ensure consistent attribution for all
# commits and comments made by the agents.

# Load the settings from the YAML file using our new utility function.
settings = yaml_utils.load_yaml_file("settings.yaml")
agents_config = settings.get("agents", {})

# Dr. Bunsen Honeydew's GitHub identity. This persona is used for conversational
# and requirements-gathering activities. The name is loaded from settings.yaml.
BUNSEN_AUTHOR = github.InputGitAuthor(
    name=agents_config.get("bunsen", {}).get("name", "Dr. Bunsen Honeydew"),
    email="bunsen@muppetslabs.com",
)

# Beaker's GitHub identity. This persona is used for coding, committing,
# and creating pull requests. The name is loaded from settings.yaml.
BEAKER_AUTHOR = github.InputGitAuthor(
    name=agents_config.get("beaker", {}).get("name", "Beaker"),
    email="beaker@muppetslabs.com",
)
