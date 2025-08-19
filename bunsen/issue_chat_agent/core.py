import dotenv
import os

from bunsen.shared import yaml_utils, personas, github_client, llms
from bunsen.issue_chat_agent import prompts


class IssueChatAgent:
    """
    The IssueChatAgent handles interactions on GitHub issues.

    This agent, embodying the persona of Dr. Bunsen Honeydew, listens for new
    comments on issues, uses a Large Language Model (LLM) to craft a response,
    and posts the response back to the issue.
    """

    def __init__(self):
        """
        Initializes the IssueChatAgent by setting up the GitHub client,
        LLM configuration, and agent persona.
        """
        # Load settings from the YAML file
        self.settings = yaml_utils.load_yaml_file("settings.yaml")

        # Load environment variables from a .env file
        dotenv.load_dotenv()

        self.github_token = os.getenv("GITHUB_TOKEN")
        self.llm_provider = llms.get_llm_provider(agent="bunsen")
        self.llm_api_url = self.settings.get("llm", {}).get("api_url", None)
        self.llm_api_key = os.getenv("LLM_API_KEY")

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set.")
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY environment variable not set.")

        # Initialize the GitHub client
        self.github_client = github_client.GitHubClient(token=self.github_token)

        # Get the LLM model name from settings and initialize the model
        model_name = self.settings.get("llm", {}).get("bunsen_model_name")

        if not model_name:
            raise ValueError("bunsen_model_name not found in settings.yaml")

        # Set the agent's persona
        self.agent_persona = personas.BUNSEN_AUTHOR
        self.agent_name = self.agent_persona._identity.get("name")

    def _get_issue_data(self, repo_name: str, issue_id: int):
        """
        Retrieves the issue and all associated comments.

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
        """
        Checks if the agent has already commented on the issue.

        Args:
            comments (list): A list of comment objects.

        Returns:
            bool: True if the agent has commented, False otherwise.
        """
        return any(comment.user.login == self.agent_persona._identity.get("name") for comment in comments)

    def _get_llm_response(self, prompt: str):
        """
        Calls the LLM to generate a response based on the prompt.

        Args:
            prompt (str): The prompt to send to the LLM.

        Returns:
            str: The generated response from the LLM, or None if an error occurs.
        """
        try:
            self.llm_provider.chat(
                messages=[{"role": "user", "content": prompt}]
            )

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return None

    def run(self, repo_name: str, issue_id: int):
        """
        The main method to run the agent's logic on a specific issue.

        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repo').
            issue_id (int): The ID of the GitHub issue to process.
        """
        print(
            f"Processing issue #{issue_id} in repository '{repo_name}' with Dr. Bunsen..."
        )

        issue, comments = self._get_issue_data(repo_name, issue_id)
        if not issue:
            return

        # Check if Bunsen has already commented on the issue
        if self._has_agent_commented(comments):
            print("Dr. Bunsen has already responded to this issue. Skipping.")
            return

        # Build the prompt for the LLM using the prompts module
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
            self.github_client.post_comment(repo_name, issue_id, comment_body)
