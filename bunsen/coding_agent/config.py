import os
from dataclasses import dataclass
import dotenv

from bunsen.shared import yaml_utils


@dataclass
class CodingAgentConfig:
    """
    A dataclass to hold the configuration settings for the CodingAgentRunner.

    This class centralizes all the necessary configuration values, such as the
    LLM model to use and the GitHub repository details, ensuring they are
    easily accessible and type-hinted.
    """
    llm_provider: str
    llm_model_name: str
    llm_api_url: str
    github_repo_url: str
    github_token: str
    github_agent_name: str

    @classmethod
    def from_settings(cls, settings_path: str = "settings.yaml") -> "CodingAgentConfig":
        """
        Loads the configuration from environment variables (.env) and a settings.yaml file.

        Args:
            settings_path (str): The path to the settings YAML file.
        """
        dotenv.load_dotenv()
        settings = yaml_utils.load_yaml_file(settings_path)

        # Get values from environment variables
        github_token = os.getenv("GITHUB_TOKEN")
        llm_provider = settings.get("llm", {}).get("provider", "google")
        llm_api_url = settings.get("llm", {}).get("api_url", None)
        llm_api_key = os.getenv("LLM_API_KEY")

        # Get values from settings.yaml
        github_repo_url = settings.get("github", {}).get("github_repo_url")
        beaker_agent_name = settings.get("agents", {}).get("beaker", {}).get("name")
        beaker_llm_model_name = settings.get("llm", {}).get("beaker_model_name")

        # Ensure required variables are present
        if not github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables.")
        if not github_repo_url:
            raise ValueError("github_repo_url not found in settings.yaml.")
        if not beaker_agent_name:
            raise ValueError("beaker agent name not found in settings.yaml.")
        if not beaker_llm_model_name:
            raise ValueError("beaker LLM model name not found in settings.yaml.")
        if not llm_api_key:
            raise ValueError("LLM_API_KEY not found in environment variables.")

        return cls(
            llm_provider=llm_provider,
            llm_model_name=beaker_llm_model_name,
            llm_api_url=llm_api_url,
            github_repo_url=github_repo_url,
            github_token=github_token,
            github_agent_name=beaker_agent_name
        )
