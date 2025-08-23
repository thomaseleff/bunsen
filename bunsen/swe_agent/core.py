"""Beaker swe-agent runner"""

from github import GithubException
import json
import os
from pathlib import Path
import re
import subprocess

from bunsen.shared import github, settings


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

    def _parse_trajectory_location(stdout) -> str:
        """Parses the trajectory file location from swe-agent.

        Args:
            stdout (str): The standard-output from the swe-agent.

        Returns:
            str: The trajectory file output location.
        """

        # Define a regex pattern to match the trajectory file path
        pattern = r"Trajectory will be saved to(.*?)\.traj"

        # Search for the pattern in the output
        match = re.search(pattern, stdout, re.DOTALL)

        if match:
            trajectory_path = match.group(1)
            return str(trajectory_path).strip() + ".traj"
        else:
            return None

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
        print(f"Beaker (swe-agent) started working on issue #{issue_id} in repository '{repo_name}'.")

        try:

            # Construct the command to run the Beaker swe-agent
            cmd = [
                "sweagent",
                "run",
                "--config",
                settings.DEFAULT_SWE_AGENT_SETTINGS_PATH,
                "--agent.model.name",
                model_name,
                "--env.repo.github_url",
                repo_url,
                "--problem_statement.github_url",
                f"{repo_url}/issues/{str(issue_id)}",
                "--actions.open_pr",
                "True",
            ]

            # Copy the environment variables containing the
            #   credentials for the LLM provider

            env = os.environ.copy()

            # Run the beaker swe-agent
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

            # Handle run-time errors
            if result.returncode != 0:
                raise RuntimeError(
                    f"    Command      : {' '.join(cmd)}\n"
                    f"    Exit-code    : {result.returncode}\n"
                    f"    Error-output : {result.stderr.strip()}"
                )

            # Retrieve the trajectory file
            trajectory_path = self._parse_trajectory_location(stdout=result.stdout)

            # Load the trajectory file
            if Path(trajectory_path).exists():
                with open(trajectory_path, "r") as f:
                    trajectory = json.load(f)

                # Retrieve the status
                submitted = trajectory.get("info", {}).get("submission", False)
                status = trajectory.get("info", {}).get("exit_status", False)
                stats = trajectory.get("info", {}).get("model_stats")

                self.github_client.post_comment(
                    repo_name=repo_name,
                    issue_id=issue_id,
                    comment_body=(
                        "Beaker (swe-agent) finished working on the issue.\n\n"
                        "```\n"
                        f"    Status    : '{status}'\n"
                        f"    Submitted : {submitted}\n"
                        f"    Stats     : {json.dumps(stats, indent=2)}\n"
                        "```\n"
                    )
                )

            else:
                raise Exception(
                    "    Status    : 'Unknown Error'\n"
                    "    Submitted : False\n"
                    "    Stats     : None"
                )

            print("Beaker (swe-agent) finished working on issue #{issue_id} in repository '{repo_name}'.")

        except subprocess.CalledProcessError as e:
            print(f"SWE-agent CLI error: {e}")
            print("Captured stdout:")
            print(e.stdout)
            print("Captured stderr:")
            print(e.stderr)
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "Beaker (swe-agent) encountered an `swe-agent` CLI error while trying to resolve the issue."
                    f"\n\n```\n{e}\n```\n"
                )
            )
        except GithubException as e:
            print(f"GitHub API error: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "Beaker (swe-agent) encountered a GitHub API error while trying to resolve the issue."
                    f"\n\n```\n{e}\n```\n"
                )
            )
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "Beaker (swe-agent) encountered an unexpected error while trying to resolve the issue."
                    f"\n\n```\n{e}\n```\n"
                )
            )
