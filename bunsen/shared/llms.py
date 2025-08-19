from typing import Any, Dict, Literal
import litellm
import dotenv

from bunsen.shared import yaml_utils


class Provider:

    def __init__(self, model_name: str):
        self.model_name = model_name

        dotenv.load_dotenv()

    def chat(self, messages: list[dict]) -> Any:
        """
        Send a chat/completion request using litellm.
        messages: list of dicts in OpenAI format [{"role": "user", "content": "..."}, ...]
        """
        # Prepare litellm parameters
        params = {
            "model": self.model_name,
            "messages": messages,
        }

        # Call litellm
        response = litellm.completion(**params)

        return response


def load_llm_config() -> Dict[str, Any]:

    # Load settings.yaml
    settings = yaml_utils.load_yaml_file("settings.yaml")

    return {
        "bunsen_model_name": settings.get("llm", {}).get("bunsen_model_name"),
        "beaker_model_name": settings.get("llm", {}).get("beaker_model_name"),
    }


def get_llm_provider(
    agent: Literal["bunsen", "beaker"],
) -> Provider:

    # Load the LLM configuration
    config = load_llm_config()

    return Provider(
        model_name=config["bunsen_model_name"] if agent == "bunsen" else config["beaker_model_name"],
    )
