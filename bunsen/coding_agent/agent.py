import os
import sys
import argparse

from bunsen.coding_agent import config, runner


def main():
    """
    Main entry point for the CodingAgent from the command line.

    This function parses command-line arguments and initializes the agent.
    """
    parser = argparse.ArgumentParser(description="Run the Coding Agent.")
    parser.add_argument("issue_id", type=int, help="The GitHub issue ID to implement, test, and commit.")

    args = parser.parse_args()

    # Get the repository name from environment variables
    repo_name = os.getenv("GITHUB_REPOSITORY")

    if not repo_name:
        print("Error: GITHUB_REPOSITORY environment variable not set.")
        sys.exit(1)

    try:
        agent = runner.CodingAgentRunner(
            config=config.CodingAgentConfig.from_settings(
                settings_path="settings.yaml",
            )
        )
        agent.run(issue_id=args.issue_id)
    except ValueError as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
