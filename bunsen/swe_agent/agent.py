"""Beaker swe-agent service"""

import argparse
import sys

from bunsen.shared import settings
from bunsen.swe_agent import core


def main():
    """Main entry point for the Beaker swe-agent from the command line.

    This function parses command-line arguments and initializes the agent.
    """

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Dispatch the Beaker swe-agent.")
    parser.add_argument("--repo_name", type=str, help="The GitHub repository name in the format `{owner}/{repo}`.")
    parser.add_argument("--installation_id", type=int, help="The GitHub App installation ID to use for authentication.")
    parser.add_argument("--issue_id", type=int, help="The GitHub issue ID to implement, test, and commit.")
    args = parser.parse_args()

    try:

        # Initialize the Beaker swe-agent
        beaker = core.Beaker(
            app_id=settings.GITHUB_APP_ID,
            private_key=settings.GITHUB_PRIVATE_KEY,
            installation_id=args.installation_id,
        )

        # Dispatch the Beaker swe-agent workflow
        beaker.dispatch(
            repo_name=args.repo_name,
            repo_url=settings.GITHUB_REPO_URL,
            issue_id=args.issue_id,
            model_name=settings.BEAKER_MODEL_NAME,
        )

    except ValueError as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
