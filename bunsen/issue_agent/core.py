"""Bunsen issue-agent actions"""

from github import Issue, IssueComment
import re

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

    def _get_issue_data(self, repo_name: str, issue_id: int) -> tuple[Issue.Issue, list[IssueComment.IssueComment]]:
        """Retrieves the issue and all associated comments.

        Args:
            repo_name (str): The name of the GitHub repository.
            issue_id (int): The ID of the issue.

        Returns:
            tuple: A tuple containing the issue object and a list of comment objects.
        """
        issue = self.github_client.get_issue(repo_name, issue_id)
        if not issue:
            return None, None

        comments = self.github_client.get_issue_comments(repo_name, issue_id)
        return issue, comments

    def _get_issue_author(self, issue: Issue.Issue) -> str:
        """Retrieves the author of the Github issue.

        Args:
            issue (github.Issue.Issue): The Github issue object.

        Returns:
            str: The name of the Github issue author.
        """
        return issue.user.login

    def _get_issue_commenters(self, comments: list[IssueComment.IssueComment]) -> list[str]:
        """Retrieves the list of Github issue commenters.

        Args:
            comments (github.IssueComment.IssueComment): The list of Github issue comment objects.

        Returns:
            list: The unique list of Github issue commenters.
        """
        if not comments:
            return []

        # Sort the comments from oldest to newest
        comments = sorted(comments, key=lambda c: c.created_at)

        # Retain the commenters based on the order they first commented
        comment_authors = []
        for comment in comments:
            if (
                comment.user.login not in comment_authors
                and comment.user.login != self.agent_name  # Do not include the agent-name
            ):
                comment_authors.append(comment.user.login)

        return comment_authors

    def _get_issue_latest_commenter(self, comments: list[IssueComment.IssueComment]) -> str:
        """Retrieves the most recent Github issue commenter who mentioned the agent.

        Args:
            comments (github.IssueComment.IssueComment): The list of Github issue comment objects.

        Returns:
            str: The name of the latest Github issue commenter who mentioned the agent.
        """

        # Define the regex pattern to search for the agent-name
        pattern = rf'@{re.escape(self.agent_name)}'

        # Filter comments that mention the agent
        comments = [
            comment for comment in comments if re.search(pattern, comment.body)
        ]

        # Get the most recent comment that mentions the agent
        most_recent_comment = max(comments, key=lambda c: c.created_at)

        return most_recent_comment.user.login if most_recent_comment else None

    def _get_issue_participants(self, issue: Issue.Issue, comments: list[IssueComment.IssueComment]) -> list[str]:
        """Retrieves the author of the Github issue.

        Args:
            issue (github.Issue.Issue): The Github issue object.
            comments (github.IssueComment.IssueComment): The list of Github issue comment objects.

        Returns:
            list: A list of Github issue participants.
        """

        # Define the regex pattern to search for GitHub usernames (e.g., @username)
        pattern = r'@(\w+)'

        # Search in the issue body
        issue_participants = re.findall(pattern, issue.body)

        # Search in each comment body
        comment_participants = []
        if comments:
            for comment in comments:
                comment_participants.extend(re.findall(pattern, comment.body))

        # Retain a unique list of issue participants
        participants = set(issue_participants + comment_participants)

        # Remove the agent-name
        if self.agent_name in participants:
            participants.remove(self.agent_name)

        return participants

    def _get_issue_team_members(
        self,
        issue: Issue.Issue,
        comments: list[IssueComment.IssueComment]
    ) -> tuple[str, str, list[str], list[str]]:
        """Retrieves the author of the Github issue

        Args:
            issue (github.Issue.Issue): The Github issue object.
            comments (github.IssueComment.IssueComment): The list of Github issue comment objects.

        Returns:
            tuple: A tuple of user names, ({primary}, {author}, {commenters}, {participants})
        """

        # Retrieve the issue author
        author = self._get_issue_author(issue=issue)

        # Retrieve the list of issue commenters
        commenters = self._get_issue_commenters(comments=comments)

        # Retrieve the list of issue participants
        participants = self._get_issue_participants(issue=issue, comments=comments)

        # Retrieve the most recent commenter who mentioned the agent
        primary = self._get_issue_latest_commenter(comments=comments)

        # Remove the issue-athor and primary commenter from the commenters
        #   and participants to avoid duplicate mentions

        for participant in [author, primary]:
            if participant:
                commenters.remove(participant)
                participants.remove(participant)

        return tuple(
            primary if primary else author,
            author,
            commenters,
            participants,
        )

    def _has_agent_commented(self, comments: list[IssueComment.IssueComment]):
        """Checks if the agent has already commented on the issue.

        Args:
            comments (list): A list of comment objects.

        Returns:
            bool: True if the agent has commented, False otherwise.
        """
        return any(comment.user.login == self.agent_name for comment in comments)

    def _agent_should_respond(
        self,
        issue: Issue.Issue,
        comments: list[IssueComment.IssueComment]
    ) -> tuple[str, str, list[str], list[str]]:
        """Determines whether the Bunsen issue-agent should respond.

        Args:
            issue (github.Issue.Issue): The Github issue object.
            comments (github.IssueComment.IssueComment): The list of Github issue comment objects.

        Returns:
            bool: True if the Bunsen issue-agent should respond, false otherwise.
        """

        # Define the regex pattern to search for the agent-name
        pattern = rf'@{re.escape(self.agent_name)}'

        # Respond if the Bunsen issue-agent is mentioned in the issue body and there are
        #   no comments yet

        if not comments:
            if re.search(pattern, issue.body):
                return True

        # Respond if there are issue comments and the Bunsen issue-agent is mentioned in the latest
        #   comment

        else:
            most_recent_comment = max(comments, key=lambda c: c.created_at)
            if re.search(pattern, most_recent_comment.body):
                return True

        return False

    def _get_llm_response(self, role: str, prompt: str):
        """Calls the LLM to generate a response based on the prompt.

        Args:
            role (str): The role of the LLM.
            prompt (str): The prompt to send to the LLM.

        Returns:
            str: The generated response from the LLM, or None if an error occurs.
        """
        try:
            response = llms.chat(
                model=self.llm_model,
                messages=[{"role": role, "content": prompt}]
            )

            # Return the message content from the llm response
            #   The llm response is always in the openai format

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return None

    def comment(self, repo_name: str, issue_id: int):
        """The main method to run the issue-agent's logic on a specific issue.

        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repository').
            issue_id (int): The ID of the GitHub issue to process.
        """
        print(
            f"Processing issue #{issue_id} in repository '{repo_name}' with the Bunsen issue-agent..."
        )

        issue, comments = self._get_issue_data(repo_name, issue_id)

        if not issue:
            print(f"Issue #{issue_id} does not exist in repository '{repo_name}'.")
            return

        # Determine whether the Bunsen issue-agent has been requested

        #   If the Bunsen issue-agent is mentioned in the issue body and there are
        #       no comments yet, respond to the issue.
        #   If there are issue comments and the Bunsen issue-agent is mentioned in the latest
        #       comment, respond to the issue.
        #   Otherwise, skip the request.

        if not self._agent_should_respond(issue=issue, comments=comments):
            print("The Bunsen issue-agent was not mentioned in the issue and will not respond.")
            return

        # Build the prompt for the LLM
        issue_body = issue.body if issue.body else "No description provided."
        issue_comments = "\n\n".join(
            f"[{comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}] **{comment.user.login}** said: {comment.body}"
            for comment in comments
        )
        prompt = prompts.get_issue_response_prompt(
            agent_name=self.agent_name,
            issue_title=issue.title,
            issue_body=issue_body,
            issue_comments=issue_comments,
        )
        print(f"The Bunsen issue-agent prompt is: {prompt}")

        # Get the LLM's response
        llm_response = self._get_llm_response(
            role=prompts.ISSUE_AGENT_ROLE,
            prompt=prompt
        )

        if llm_response:

            # Get the issue participants
            primary, _, _, participants = self._get_issue_participants(
                issue=issue,
                comments=comments,
            )

            # Post the response as a comment on the issue
            comment_body = f"@{primary}\n\n{llm_response}\n\ncc {", ".join([f"@{p}" for p in participants])}"
            self.github_client.post_comment(
                repo_name=repo_name,
                issue_id=issue_id,
                comment_body=comment_body
            )
            print(f"The Bunsen issue-agent response is: {llm_response}.")

    def dispatch_coding_agent(self, repo_name: str, issue_id: int):
        """Dispatches the coding agent workflow for the issue.

        Args:
            repo_name (str): The full name of the repository (e.g., 'owner/repository').
            issue_id (int): The ID of the GitHub issue to process.
        """

        # Dispatch the coding agent workflow
        self.github_client.run_workflow_dispatch(
            repo_name=repo_name,
            workflow_filename=settings.GITHUB_CODING_WORKFLOW_FILENAME,
            issue_id=issue_id,
            branch=settings.GITHUB_MAIN_BRANCH,
        )

        # Update the Github issue with progress
        self.github_client.post_comment(
            repo_name=repo_name,
            issue_id=issue_id,
            comment_body=(
                "Beaker (swe-agent) has been assigned to resolve this issue."
                f" You can track the progress via [Github Actions](https://github.com/{repo_name}/actions)."
            ),
        )
