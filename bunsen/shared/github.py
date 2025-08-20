"""Github client"""

import requests
from github import Github, Auth, GithubException, Repository, Issue, IssueComment
import urllib.parse as urlparse


class Client:
    """A `class` object that represents a Python client to interact with the GitHub API."""

    def __init__(
        self,
        app_id: str,
        private_key: str,
        installation_id: int,
    ):
        """Initializes the GitHub client.

        Args:
            app_id (str): The ID of the GitHub App.
            private_key (str): The private key for the GitHub App.
            installation_id (int): The ID of the specific installation to act on behalf of.
        """
        try:
            # Authenticate as the GitHub App
            app_auth = Auth.AppAuth(app_id, private_key)

            # Retrieve a temporary installation access token
            self.g = Github(auth=app_auth.get_installation_auth(installation_id))

            # Retain the installation ID and token for API requests
            self.installation_id = installation_id
            self.installation_token = app_auth.get_installation_auth(installation_id).token

            # Retain the Github App user
            self.user = self.g.get_user().login

            print(f"Successfully authenticated as `{self.user}`.")

        except Exception as e:
            print(f"Error authenticating to GitHub: {e}")
            raise

    def _parse_repo_metadata_from_url(self, repo_url: str) -> tuple[str, str] | None:
        """A private helper method to parse the repository owner and name from a URL.

        Args:
            repo_url (str): The URL of the repository (e.g., 'https://github.com/{owner}/{repo}').

        Returns:
            tuple[str, str] | None: A tuple containing the repository owner and name,
            or None if the URL is invalid.
        """
        try:
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1]
                return (owner, repo)
            return None
        except Exception as e:
            print(f"Error parsing repository URL: {e}")
            return None

    def get_repo(self, repo_name: str) -> Repository.Repository | None:
        """Retrieves a GitHub repository object.

        Args:
            repo_name (str): The full name of the repository (e.g., 'octocat/hello-world').

        Returns:
            github.Repository.Repository: The repository object.
        """
        try:
            repo = self.g.get_repo(repo_name)
            return repo
        except GithubException as e:
            print(f"Error getting repository '{repo_name}': {e}")
            return None

    def get_issue(self, repo_name: str, issue_id: int) -> Issue.Issue | None:
        """Retrieves a specific GitHub issue from a repository.

        Args:
            repo_name (str): The full name of the repository (e.g., 'octocat/hello-world').
            issue_id (int): The id of the issue to retrieve.

        Returns:
            github.Issue.Issue: The issue object.
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                issue = repo.get_issue(number=issue_id)
                return issue
            except GithubException as e:
                print(f"Error getting issue #{issue_id} from '{repo_name}': {e}")
                return None
        return None

    def get_issue_comments(self, repo_name: str, issue_id: int) -> list[IssueComment.IssueComment]:
        """Retrieves all comments for a specific GitHub issue.

        Args:
            repo_name (str): The full name of the repository.
            issue_id (int): The number of the issue.

        Returns:
            list[github.IssueComment.IssueComment]: A list of comment objects.
        """
        issue = self.get_issue(repo_name, issue_id)
        if issue:
            try:
                return list(issue.get_comments())
            except GithubException as e:
                print(f"Error getting comments for issue #{issue_id}: {e}")
                return []
        return []

    def post_comment(self, repo_name: str, issue_id: int, comment_body: str):
        """Adds a comment to a GitHub issue or pull request.

        Args:
            repo_name (str): The full name of the repository.
            issue_id (int): The number of the issue or pull request.
            comment_body (str): The markdown-formatted body of the comment.
        """
        issue = self.get_issue(repo_name, issue_id)
        if issue:
            try:
                issue.create_comment(comment_body)
                print(f"Successfully added comment to issue #{issue.number}")
            except GithubException as e:
                print(f"Error adding comment to issue #{issue.number}: {e}")

    def add_label_to_issue(self, repo_name: str, issue_id: int, label_name: str):
        """Adds a label to a GitHub issue. This is a key way to communicate status and trigger workflows,
        like signaling that a task is 'ready-for-dev'.

        Args:
            repo_name (str): The full name of the repository.
            issue_id (int): The number of the issue.
            label_name (str): The name of the label to add.
        """
        issue = self.get_issue(repo_name, issue_id)
        if issue:
            try:
                issue.add_to_labels(label_name)
            except GithubException as e:
                print(f"Error adding label to issue #{issue_id}: {e}")

    def run_workflow_dispatch(self, repo_name: str, workflow_filename: str, issue_id: int, branch: str = "main"):
        """Triggers a GitHub Actions workflow using the 'workflow_dispatch' event
        for the given repository and workflow filename.

        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repo').
            workflow_filename (str): The filename of the workflow to dispatch (e.g., 'swe_agent.yaml').
            issue_id (int): The ID of the GitHub issue to process.
            branch (str): The branch to trigger the workflow on. Defaults to 'main'.
        """
        try:
            url = f"https://api.github.com/repos/{repo_name}/actions/workflows/{workflow_filename}/dispatches"

            data = {
                "ref": branch,
                "inputs": {
                    "repo_name": repo_name,
                    "installation_id": str(self.installation_id),
                    "issue_id": str(issue_id)
                }
            }

            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {self.installation_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 204:
                print(f"Successfully triggered workflow '{workflow_filename}' for issue #{issue_id}")
            else:
                print(f"Failed to trigger workflow: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"An error occurred while triggering the workflow: {e}")

    def get_repository_content(
        self, repo_name: str, path: str, branch: str = "main"
    ) -> str | None:
        """Retrieves the content of a file from a repository.

        Args:
            repo_name (str): The full name of the repository.
            path (str): The path to the file within the repository (e.g., 'README.md').
            branch (str): The branch to retrieve the content from. Defaults to 'main'.

        Returns:
            str: The content of the file as a string, or None if the file is not found.
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                contents = repo.get_contents(path, ref=branch)
                return contents.decoded_content.decode("utf-8")
            except GithubException as e:
                print(
                    f"Error getting content for path '{path}' on branch '{branch}': {e}"
                )
                return None
        return None
