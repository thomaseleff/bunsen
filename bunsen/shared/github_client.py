from github import Github, GithubException, InputGitAuthor


class GitHubClient:
    """
    A client to interact with the GitHub API, acting as the 'central nervous system'
    for the Bunsen and Beaker agents. This class encapsulates all API calls,
    making the main application logic clean and modular.

    This is Dr. Bunsen's personal assistant, responsible for fetching information
    and executing commands on the GitHub platform without causing a scene.
    """

    def __init__(self, token: str):
        """
        Initializes the GitHub client with a personal access token.

        Args:
            token (str): A GitHub Personal Access Token (PAT) with the necessary permissions.
        """
        try:
            self.g = Github(token)
            self.user = self.g.get_user()
            print(f"Successfully connected to GitHub as user: {self.user.login}")
        except GithubException as e:
            print(f"Error connecting to GitHub: {e}")
            raise

    def get_repo(self, repo_name: str):
        """
        Retrieves a GitHub repository object.

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

    def get_issue(self, repo_name: str, issue_id: int):
        """
        Retrieves a specific GitHub issue from a repository.
        This is how Dr. Bunsen gets the full context of a problem.

        Args:
            repo_name (str): The full name of the repository (e.g., 'octocat/hello-world').
            issue_id (int): The number of the issue to retrieve.

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

    def get_issue_comments(self, repo_name: str, issue_id: int):
        """
        Retrieves all comments for a specific GitHub issue.
        This allows Dr. Bunsen to read the full conversation history.

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
        """
        Adds a comment to a GitHub issue or pull request.
        This is how Dr. Bunsen and Beaker provide updates and responses.

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
        """
        Adds a label to a GitHub issue.
        This is a key way to communicate status and trigger workflows,
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
                print(f"Successfully added label '{label_name}' to issue #{issue_id}")
            except GithubException as e:
                print(f"Error adding label to issue #{issue_id}: {e}")

    def get_repository_content(
        self, repo_name: str, path: str, branch: str = "main"
    ):
        """
        Retrieves the content of a file from a repository.
        This allows Beaker to read existing code and documentation.

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

    def create_branch(
        self, repo_name: str, new_branch_name: str, base_branch: str = "main"
    ):
        """
        Creates a new branch from a base branch.
        This is Beaker setting up its own workbench.

        Args:
            repo_name (str): The full name of the repository.
            new_branch_name (str): The name of the new branch to create.
            base_branch (str): The branch to create the new one from. Defaults to 'main'.

        Returns:
            github.GitRef.GitRef: The new Git reference object, or None if an error occurred.
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                base_ref = repo.get_git_ref(f"heads/{base_branch}")
                new_ref = repo.create_git_ref(
                    ref=f"refs/heads/{new_branch_name}", sha=base_ref.object.sha
                )
                print(
                    f"Successfully created branch '{new_branch_name}' from '{base_branch}'"
                )
                return new_ref
            except GithubException as e:
                print(f"Error creating branch '{new_branch_name}': {e}")
                return None
        return None

    def create_commit(
        self,
        repo_name: str,
        branch: str,
        commit_message: str,
        file_updates: dict,
        author: InputGitAuthor,
    ):
        """
        Commits changes to a specific branch.
        This is how Beaker saves its work, with proper attribution.

        Args:
            repo_name (str): The full name of the repository.
            branch (str): The branch to commit to.
            commit_message (str): The message for the new commit.
            file_updates (dict): A dictionary where keys are file paths and values are the new file contents (as strings).
            author (InputGitAuthor): The author of the commit, allowing explicit attribution.

        Returns:
            github.GitCommit.GitCommit: The new commit object, or None if an error occurred.
        """
        repo = self.get_repo(repo_name)
        if not repo:
            return None

        try:
            # Get the base branch reference and latest commit SHA
            base_ref = repo.get_git_ref(f"heads/{branch}")
            base_sha = base_ref.object.sha

            # Get the base tree for the new commit
            base_tree = repo.get_git_tree(sha=base_sha)

            # Create a new tree with the updated file contents
            new_tree_elements = []
            for path, content in file_updates.items():
                blob = repo.create_git_blob(content, "utf-8")
                new_tree_elements.append(
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob.sha,
                    }
                )

            # Create a new tree with the new elements and parent tree
            new_tree = repo.create_git_tree(new_tree_elements, base_tree)

            # Create a new commit object with the specified author
            new_commit = repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[repo.get_git_commit(base_sha)],
                author=author,
            )

            # Update the branch reference to point to the new commit
            base_ref.edit(sha=new_commit.sha)

            print(f"Successfully committed changes to branch '{branch}'")
            return new_commit

        except GithubException as e:
            print(f"Error creating commit: {e}")
            return None

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        reviewers: list = [],
    ):
        """
        Creates a new pull request in a repository and requests reviews.
        This is Beaker's final output, a proposal for a change, ready for human review.

        Args:
            repo_name (str): The full name of the repository.
            title (str): The title for the new pull request.
            body (str): The markdown-formatted body of the pull request description.
            head_branch (str): The name of the branch with the changes (the 'head').
            base_branch (str): The name of the branch to merge into (the 'base', typically 'main').
            reviewers (list): A list of GitHub usernames to request reviews from.

        Returns:
            github.PullRequest.PullRequest: The created pull request object, or None if an error occurred.
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                pull = repo.create_pull(
                    title=title, body=body, head=head_branch, base=base_branch
                )
                print(f"Successfully created pull request: '{pull.title}'")

                if reviewers:
                    try:
                        pull.create_review_request(reviewers=reviewers)
                        print(f"Review requests sent to: {', '.join(reviewers)}")
                    except GithubException as e:
                        print(f"Error requesting reviews: {e}")

                return pull
            except GithubException as e:
                print(f"Error creating pull request: {e}")
                return None
        return None
