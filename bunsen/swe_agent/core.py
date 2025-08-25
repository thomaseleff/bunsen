"""Beaker swe-agent runner"""

from github import GithubException
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
from textwrap import dedent
import traceback

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

    def _parse_trajectory_location(self, stdout) -> str:
        """Parses the trajectory file location from swe-agent.

        Args:
            stdout (str): The standard-output from the swe-agent.

        Returns:
            str: The trajectory file output location.
        """

        # Remove indentation
        stdout = dedent(stdout)

        # Define a regex pattern to match the trajectory file path
        pattern = re.compile(r'Trajectory will be saved to([\s\S]*?\.traj)', re.DOTALL)

        # Search for the pattern in the output
        match = pattern.search(stdout)

        if match:
            trajectory_path = re.sub(r'\s+', '', match.group(1))
            return str(trajectory_path).strip()
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
        print(f"beaker-swe-agent started working on issue #{issue_id} in repository '{repo_name}'.")

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
                encoding="utf-8",
                errors="ignore",
                env=env
            )

            print("swe-agent stdout:")
            print(result.stdout)

            # if result.stdout:
            #     with open(Path.cwd() / "stdout.txt", 'w', encoding="utf-8") as f:
            #         f.write(result.stdout)

            print("swe-agent stderr:")
            print(result.stderr)

            # if result.stderr:
            #     with open(Path.cwd() / "stderr.txt", 'w', encoding="utf-8") as f:
            #         f.write(result.stderr)

            # Handle run-time errors
            if result.returncode != 0:
                raise RuntimeError(
                    f"- Command : `{' '.join(cmd)}`\n"
                    f"- Exit-code : {result.returncode}\n"
                    "- Error-output : \n\n"
                    "```\n"
                    f"{result.stderr.strip()}\n"
                    "```\n"
                )

            # Retrieve the trajectory file
            trajectory_path = self._parse_trajectory_location(stdout=result.stdout)

            # Load the trajectory file
            if Path(trajectory_path).exists():
                with open(trajectory_path, "r") as f:
                    trajectory = json.load(f)

                # Retrieve the status
                status = trajectory.get("info", {}).get("exit_status", False)
                patch = trajectory.get("info", {}).get("submission", False)
                stats = trajectory.get("info", {}).get("model_stats")

                # Retrieve the patch
                patch_path = str(Path(trajectory_path).with_suffix('.patch'))

                self.github_client.post_comment(
                    repo_name=repo_name,
                    issue_id=issue_id,
                    comment_body=(
                        "beaker-swe-agent finished working on the issue.\n\n"
                        f"- Status : `{status}`\n"
                        "- Stats : \n\n"
                        "```\n"
                        f"{json.dumps(stats, indent=4)}\n"
                        "```\n"
                        f"- Patch : `{patch_path}`\n\n"
                        "**Patch (diff)**\n\n"
                        "```\n"
                        f"{patch}\n"
                        "```\n"
                    )
                )

                # Set output
                print(f"::set-output name=patch_path::{patch_path}")
                print(f"::set-output name=exit_status::{status}")

            else:
                raise FileNotFoundError(
                    f"beaker-swe-agent finished working on issue #{issue_id}"
                    f" in repository '{repo_name}' but there is no trajectory file available."
                )

            print(f"beaker-swe-agent finished working on issue #{issue_id} in repository '{repo_name}'.")

        except RuntimeError as e:
            print(f"swe-agent CLI error: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "beaker-swe-agent encountered an `swe-agent` CLI error while trying to resolve the issue."
                    f"\n\n`{e}`\n"
                )
            )
        except GithubException as e:
            print(f"GitHub API error: {e}")
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "beaker-swe-agent encountered a GitHub API error while trying to resolve the issue."
                    f"\n\n`{e}`\n"
                )
            )
        except Exception as e:

            # Retrieve the exception information
            exception = (
                f"- Filename : {inspect.trace()[-1][1]}\n"
                f"- Line Number : Line {inspect.trace()[-1][2]}\n"
                f"- Function : `{inspect.trace()[-1][3]}()`\n"
                f"- Exception : `{type(e).__name__}`\n"
            )

            print(f"An unexpected error occurred:\n\n{type(e).__name__}: {e}")

            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=(
                    "beaker-swe-agent encountered an unexpected error while trying to resolve the issue.\n\n"
                    f"`{type(e).__name__}: {e}`\n\n"
                    f"{exception}\n\n"
                    "**Traceback**\n\n"
                    "```\n"
                    f"{traceback.format_exc()}\n"
                    "```\n"
                )
            )
