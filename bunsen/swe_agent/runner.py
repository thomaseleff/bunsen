"""Beaker swe-agent runner"""

import os
from github import GithubException
import subprocess

from bunsen.shared import github
from bunsen.swe_agent import prompts


class Beaker:
    """Orchestrates the Beaker swe-agent workflow, acting as an entry point for
    GitHub Actions.
    """

    def __init__(self, app_id: str, private_key: str, installation_id: int):
        """Initializes the Beaker swe-agent.

        Args:
            app_id (str): The ID of the GitHub App.
            private_key (str): The private key for the GitHub App.
            installation_id (int): The ID of the specific installation to act on behalf of.
        """

        # Initialize the GitHub client with GitHub App credentials
        self.github_client = github.Client(
            app_id=app_id,
            private_key=private_key,
            installation_id=installation_id,
        )

    def dispatch(self, repo_name: str, repo_url: str, issue_id: int, model_name: str):
        """The main entry point for the Beaker swe-agent.

        This method orchestrates the full workflow:
        1. Gets the issue information.
        2. Executes the `swe-agent` to resolve the issue via its CLI.
        3. Posts a comment to the GitHub issue with the outcome.

        Args:
            repo_name (str): The name of the GitHub repository.
            repo_url (str): The url of the GitHub repository.
            issue_id (int): The number of the GitHub issue to work on.
            model_name (str): The name of the LLM model.
        """
        print(f"Coding Agent started for issue #{issue_id} in '{repo_name}'.")

        try:

            # Retrieve the issue
            issue = self.github_client.get_issue(repo_name=repo_name, issue_id=issue_id)
            issue_title: str = issue.title
            issue_body: str = issue.body

            # Build the prompt for the LLM
            llm_plan: str = prompts.get_issue_plan_prompt(
                issue_title=issue_title,
                issue_body=issue_body,
            )
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=f"I've started working on this issue. Here is my plan:\n\n{llm_plan}",
            )

            # Construct the command to run the Beaker swe-agent
            cmd = [
                "sweagent",
                "run",
                "--agent.model.name",
                model_name,
                "--env.repo.github_url",
                repo_url,
                "--problem_statement.github_url",
                f"{repo_url}/issues/{str(issue_id)}",
            ]

            # Copy the environment variables containing the
            #   credentials for the LLM provider

            env = os.environ.copy()

            # Run the beaker swe-agent
            print("Running the Beaker swe-agent.")
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),  # The subprocess will run from the current working directory
                capture_output=True,
                text=True,
                check=True,  # Raise an exception if the command returns a non-zero exit code
                env=env
            )

            # Print the stdout and stderr for debugging
            print("SWE-agent stdout:")
            print(result.stdout)
            print("SWE-agent stderr:")
            print(result.stderr)

            print("The Beaker swe-agent finished successfully.")

            # Update the issue with the result
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body="I have successfully submitted a pull request to resolve this issue. Please review the changes."
            )

        except subprocess.CalledProcessError as e:
            print(f"SWE-agent CLI error: {e}")
            print("Captured stdout:")
            print(e.stdout)
            print("Captured stderr:")
            print(e.stderr)
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=f"I encountered a `swe-agent` CLI error while trying to fix this issue: {e}"
            )
        except GithubException as e:
            print(f"GitHub API error: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=f"I encountered a GitHub API error while trying to fix this issue: {e}"
            )
        except Exception as e:
            print(f"An unexpected error occurred during the coding agent run: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=f"I encountered an unexpected error while trying to fix this issue: {e}"
            )
