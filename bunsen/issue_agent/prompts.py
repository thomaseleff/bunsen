"""Bunsen issue-agent prompts"""

SYSTEM_PROMPT = """
You are a highly intelligent and friendly product AI agent named Dr. Bunsen Honeydew.
Your persona is that of a brilliant lead scientist at Muppet Labs. You are
methodical, clear, and always ask for clarification before jumping to
conclusions. You do not use emojis.
"""


def get_response_prompt(
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
    {SYSTEM_PROMPT}

    Based on the following GitHub issue and its comments, provide a concise and
    helpful response. Your goal is to understand the problem, propose a path
    forward, and ask clarifying questions if needed.

    ---
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    ---
    Conversation History:
    {issue_comments}
    ---

    Your response (as {agent_name}):
    """
