def get_issue_plan_prompt(issue_title: str, issue_body: str) -> str:
    """
    Generates a prompt for the LLM to create a coding plan for a GitHub issue.

    This prompt asks the LLM to act as a coding assistant and to outline a clear,
    step-by-step plan for implementing the changes described in the issue.

    Args:
        issue_title: The title of the GitHub issue.
        issue_body: The body content of the GitHub issue.

    Returns:
        A string containing the formatted prompt for the LLM.
    """
    return (
        f"You are a coding assistant that helps fix issues in software projects. "
        f"Your task is to take a GitHub issue and generate a step-by-step plan "
        f"for a developer to implement a solution. The plan should be concise "
        f"and actionable, focusing on the specific code changes required. "
        f"Do not include any conversational text, just the plan.\n\n"
        f"**Issue Title:** {issue_title}\n"
        f"**Issue Body:**\n{issue_body}\n\n"
        f"**Your Plan:**"
    )
