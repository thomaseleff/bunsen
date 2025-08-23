"""Bunsen issue-agent prompts"""

from bunsen.shared import settings

ISSUE_AGENT_SYSTEM_TEMPLATE = settings.ISSUE_AGENT.get("agent", {}).get("templates", {}).get("system_template", "")
ISSUE_AGENT_ROLE = "assistant"

SWE_AGENT_SYSTEM_TEMPLATE = settings.SWE_AGENT.get("agent", {}).get("templates", {}).get("system_template", "")
SWE_AGENT_ROLE = "assistant"


def get_issue_response_prompt(
    agent_name: str, issue_title: str, issue_body: str, issue_comments: str
) -> str:
    """Generates a prompt for the LLM to create a helpful and concise response
    to a GitHub issue.

    Args:
        agent_name (str): The name of the AI agent (e.g., "Dr. Bunsen Honeydew").
        issue_title (str): The title of the GitHub issue.
        issue_body (str): The main body content of the GitHub issue.
        issue_comments (str): The conversation history from the issue comments.

    Returns:
        str: The full prompt string to send to the LLM.
    """
    return f"""
    {ISSUE_AGENT_SYSTEM_TEMPLATE}

    Based on the following GitHub issue and its comments, provide a concise and
    helpful response as {agent_name}. Your goal is to understand the problem, propose a path
    forward, and ask clarifying questions if needed. The comments are in chronological order,
    from oldest to newest.

    ---
    Issue title: {issue_title}
    Issue body: {issue_body}
    ---
    Conversation history:
    {issue_comments}
    ---
    """
