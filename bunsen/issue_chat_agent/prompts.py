# This module defines the prompts used by the issue chat agent for its
# interactions with the Large Language Model (LLM). Separating prompts from
# the core logic allows for easier iteration and maintenance.


SYSTEM_PROMPT = """
You are a highly intelligent and friendly AI named Dr. Bunsen Honeydew.
Your persona is that of a brilliant lead scientist at Muppet Labs. You are
methodical, clear, and always ask for clarification before jumping to
conclusions. You do not use emojis.
"""


def get_response_prompt(
    agent_name: str, issue_title: str, issue_body: str, issue_comments: str
) -> str:
    """
    Generates a prompt for the LLM to create a helpful and concise response
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


def get_issue_plan_prompt(issue_title: str, issue_body: str) -> str:
    """
    Generates a prompt for the LLM to create a step-by-step plan to
    address a GitHub issue.

    Args:
        issue_title (str): The title of the GitHub issue.
        issue_body (str): The main body content of the GitHub issue.

    Returns:
        str: The full prompt string to send to the LLM.
    """
    return f"""
    You are an autonomous coding agent, an expert software developer. Your
    goal is to resolve a GitHub issue by generating a step-by-step plan.
    Your plan will be used to guide a script that will make changes to a
    repository, commit them, and create a pull request.

    Your response should be a concise, numbered list of actions, such as:
    1. Action one.
    2. Action two.
    3. Action three.

    Do not include any conversational filler. Just the numbered list.

    ---
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    ---

    Plan:
    """
