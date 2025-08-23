"""LLMs"""

from typing import Any, Literal
import litellm

from bunsen.shared import settings


# Configure litellm
#   Unsupported parameters will be dropped from the chat/completion request

litellm.drop_params = True


def chat(model: str, messages: list[dict]) -> Any:
    """Send a chat/completion request using litellm.

    Args:
        model (str): The model name to use for the request.
        messages (list[dict]): The list of dicts in OpenAI format [{"role": "user", "content": "..."}, ...]
    """

    # Prepare litellm parameters
    params = {
        "model": model,
        "messages": messages,
    }

    # Chat
    response = litellm.completion(**params)

    return response


def get_llm_model(
    agent: Literal["bunsen", "beaker"],
) -> str:
    return settings.BUNSEN_MODEL_NAME if agent == "bunsen" else settings.BEAKER_MODEL_NAME
