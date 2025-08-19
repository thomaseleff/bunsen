import subprocess
import os

from github import GithubException

from bunsen.shared import github_client
from bunsen.coding_agent import config, prompts


class CodingAgentRunner:
    """
    Orchestrates the coding agent's workflow, acting as an entry point for
    GitHub Actions.

    This class prepares the environment and executes the `swe-agent`
    workflow to resolve a GitHub issue.
    """

    def __init__(self, config: config.CodingAgentConfig):
        """
        Initializes the CodingAgentRunner with the given configuration.

        Args:
            config (CodingAgentConfig): The configuration object for the runner.
        """
        self.config = config
        self.github_client = github_client.GitHubClient(
            token=config.github_token
        )

    def run(self, issue_id: int):
        """
        The main entry point for the coding agent.

        This method orchestrates the full workflow:
        1. Gets the issue information.
        2. Executes the `swe-agent` to resolve the issue via its CLI.
        3. Posts a comment to the GitHub issue with the outcome.

        Args:
            issue_id (int): The number of the GitHub issue to work on.
        """
        repo_name = self.config.github_repo_url.split('/')[-2] + '/' + self.config.github_repo_url.split('/')[-1]
        print(f"Coding Agent started for issue #{issue_id} in '{repo_name}'.")

        try:
            # 1. Get the issue to ensure it exists and to get its details for the LLM.
            issue = self.github_client.get_issue(repo_name=repo_name, issue_id=issue_id)
            issue_title: str = issue.title
            issue_body: str = issue.body

            # 2. Use the LLM to generate a plan for the agent based on the issue details.
            llm_plan: str = prompts.get_issue_plan_prompt(
                issue_title=issue_title, issue_body=issue_body
            )
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                body=f"I've started working on this issue. Here is my plan:\n\n{llm_plan}",
            )

            # 3. Execute the SWE-agent workflow using the CLI.
            print("Executing SWE-agent via subprocess.")

            # Construct the command to run the sweagent CLI
            cmd = [
                "sweagent",
                "run",
                "--env.repo.github_url",
                self.config.github_repo_url,
                "--env.repo.issue_id",
                str(issue_id),
            ]

            # Pass the GitHub token as an environment variable for the subprocess
            env = os.environ.copy()
            env["GITHUB_TOKEN"] = self.config.github_token

            # Use subprocess.run to execute the command and capture output
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

            print("SWE-agent finished successfully.")

            # 4. Post a comment to the issue with the outcome
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                body="I have successfully submitted a pull request to resolve this issue. Please review the changes."
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
                body=f"I encountered a `swe-agent` CLI error while trying to fix this issue: {e}"
            )
        except GithubException as e:
            print(f"GitHub API error: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                body=f"I encountered a GitHub API error while trying to fix this issue: {e}"
            )
        except Exception as e:
            print(f"An unexpected error occurred during the coding agent run: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                body=f"I encountered an unexpected error while trying to fix this issue: {e}"
            )
