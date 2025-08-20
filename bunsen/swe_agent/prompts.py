"""Beaker swe-agent prompts"""

SYSTEM_PROMPT = """
You are an autonomous coding agent, an expert software developer. Your
goal is to resolve a GitHub issue by generating a step-by-step plan.
Your plan will be used to guide a script that will make changes to a
repository, commit them, and create a pull request.
"""


def get_issue_plan_prompt(issue_title: str, issue_body: str) -> str:
    """Generates a prompt for the LLM to create a step-by-step plan to
    address a GitHub issue.

    Args:
        issue_title (str): The title of the GitHub issue.
        issue_body (str): The main body content of the GitHub issue.

    Returns:
        str: The full prompt string to send to the LLM.
    """
    return f"""
    {SYSTEM_PROMPT}

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
