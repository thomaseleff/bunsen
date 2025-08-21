"""Bunsen issue-agent actions"""

from bunsen.shared import github, llms, settings
from bunsen.issue_agent import prompts


class Bunsen:
    """The Bunsen issue-agent handles interactions on GitHub issues.

    This agent, embodying the persona of Dr. Bunsen Honeydew, listens for new
    comments on issues, uses a Large Language Model (LLM) to craft a response,
    and posts the response back to the issue.
    """

    def __init__(self, app_id: str, private_key: str, installation_id: int):
        """Initializes the Bunsen issue-agent by setting up the GitHub client,
        LLM configuration, and agent persona using GitHub App credentials.

        Args:
            app_id (str): The ID of the GitHub App.
            private_key (str): The private key for the GitHub App.
            installation_id (int): The ID of the specific installation to act on behalf of.
        """

        # Initialize the GitHub client with GitHub App credentials
        self.github_client = github.Client(
            app_id=app_id,
            private_key=private_key,
            installation_id=installation_id
        )

        # Get the llm model
        self.llm_model = llms.get_llm_model(agent="bunsen")

        if not self.llm_model:
            raise ValueError("`bunsen_model_name` not found in `settings.yaml`.")

        # Set the agent name to the Github App user
        self.agent_name = self.github_client.user

    def _get_issue_data(self, repo_name: str, issue_id: int):
        """Retrieves the issue and all associated comments.

        Args:
            repo_name (str): The name of the GitHub repository.
            issue_id (int): The ID of the issue.

        Returns:
            tuple: A tuple containing the issue object and a list of comment objects.
        """
        issue = self.github_client.get_issue(repo_name, issue_id)
        if not issue:
            print(f"Issue #{issue_id} not found in repo '{repo_name}'.")
            return None, None

        comments = self.github_client.get_issue_comments(repo_name, issue_id)
        return issue, comments

    def _has_agent_commented(self, comments):
        """Checks if the agent has already commented on the issue.

        Args:
            comments (list): A list of comment objects.

        Returns:
            bool: True if the agent has commented, False otherwise.
        """
        return any(comment.user.login == self.agent_name for comment in comments)

    def _get_llm_response(self, prompt: str):
        """Calls the LLM to generate a response based on the prompt.

        Args:
            prompt (str): The prompt to send to the LLM.

        Returns:
            str: The generated response from the LLM, or None if an error occurs.
        """
        try:
            response = llms.chat(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}]
            )

            # Return the message content from the llm response
            #   The llm response is always in the openai format

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return None

    def comment(self, repo_name: str, issue_id: int):
        """The main method to run the issue agent's logic on a specific issue.

        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repo').
            issue_id (int): The ID of the GitHub issue to process.
        """
        print(
            f"Processing issue #{issue_id} in repository '{repo_name}' with the Bunsen issue-agent..."
        )

        issue, comments = self._get_issue_data(repo_name, issue_id)
        if not issue:
            return

        # Check if the Bunsen issue-agent has already commented
        if self._has_agent_commented(comments):
            print("The Bunsen issue-agent has already responded to this issue. Skipping...")
            return

        # Build the prompt for the LLM
        issue_body = issue.body if issue.body else "No description provided."
        issue_comments = "\n\n".join(
            [f"**{comment.user.login}** said: {comment.body}" for comment in comments]
        )
        prompt = prompts.get_response_prompt(
            agent_name=self.agent_name,
            issue_title=issue.title,
            issue_body=issue_body,
            issue_comments=issue_comments,
        )

        # Get the LLM's response
        llm_response = self._get_llm_response(prompt)
        if llm_response:

            # Post the response as a comment on the issue
            comment_body = f"**{self.agent_name}** said:\n\n{llm_response}"
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=comment_body
            )

    def dispatch_coding_agent(self, repo_name: str, issue_id: int):
        """Dispatches the coding agent workflow for the issue.


        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repo').
            issue_id (int): The ID of the GitHub issue to process.
        """

        # Dispatch the coding agent workflow
        self.github_client.run_workflow_dispatch(
            repo_name=repo_name,
            workflow_filename=settings.GITHUB_CODING_WORKFLOW_FILENAME,
            issue_id=issue_id,
            branch=settings.GITHUB_MAIN_BRANCH,
        )
