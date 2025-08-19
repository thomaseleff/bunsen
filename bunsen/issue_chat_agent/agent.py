import os
import hmac
import hashlib
import uvicorn
import requests
from functools import lru_cache
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import PlainTextResponse

from bunsen.issue_chat_agent.core import IssueChatAgent
from bunsen.shared import yaml_utils


# Create the FastAPI application instance.
app = FastAPI()

# Get the webhook secret from environment variables.
# This secret is used to verify that the request is from GitHub.
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Load settings to get the configurable coding trigger label
settings = yaml_utils.load_yaml_file("settings.yaml")
CODING_TRIGGER_LABEL = settings.get("github", {}).get("coding_trigger_label", "ready-for-dev")
CODING_WORKFLOW_FILENAME = "coding_agent.yaml"


@lru_cache()
def get_issue_chat_agent():
    """
    Returns a singleton instance of the IssueChatAgent.

    This uses a function with `lru_cache` to ensure the agent is initialized
    only once per process and shared across all requests.
    """
    return IssueChatAgent()


@app.get("/", status_code=200, response_class=PlainTextResponse)
def root():
    """
    A simple root endpoint to confirm the application is running.

    Returns:
        PlainTextResponse: A simple status message.
    """
    return "Issue Chat Agent is running!"


def run_workflow_dispatch(repo_name: str, issue_id: int):
    """
    Triggers a GitHub Actions workflow using the 'workflow_dispatch' event.

    This is how the issue chat agent tells the coding agent to start its work.

    Args:
        repo_name (str): The full name of the repository (e.g., 'owner/repo').
        issue_id (int): The ID of the GitHub issue to process.
    """
    try:
        # Get the GitHub token from the environment
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable not set.")
            return

        # Define the API endpoint for workflow dispatch
        url = f"https://api.github.com/repos/{repo_name}/actions/workflows/{CODING_WORKFLOW_FILENAME}/dispatches"

        # The data to send with the request, including the issue number
        data = {
            "ref": "main",  # Or the branch you want to trigger the workflow on
            "inputs": {
                "issue_id": str(issue_id)
            }
        }

        # Headers for authentication and content type
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
            "Content-Type": "application/json"
        }

        # Make the POST request to trigger the workflow
        response = requests.post(url, headers=headers, json=data)

        # Check the response status
        if response.status_code == 204:
            print(f"Successfully triggered workflow '{CODING_WORKFLOW_FILENAME}' for issue #{issue_id}")
        else:
            print(f"Failed to trigger workflow: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"An error occurred while triggering the workflow: {e}")


@app.post("/github-webhook")
async def github_webhook(request: Request):
    """
    Endpoint to receive and process GitHub webhook events.

    This function verifies the request signature and triggers the IssueChatAgent
    to process the corresponding issue.

    Args:
        request (Request): The incoming request object from FastAPI.
    """
    # Get a shared instance of the agent for this request.
    bunsen = get_issue_chat_agent()

    # Verify the webhook signature to ensure the request is from GitHub.
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(
            status_code=401, detail="X-Hub-Signature-256 header missing"
        )

    # Read the request body as bytes for HMAC verification.
    body = await request.body()
    secret_bytes = GITHUB_WEBHOOK_SECRET.encode("utf-8")
    mac = hmac.new(secret_bytes, msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(
            status_code=403, detail="X-Hub-Signature-256 header is invalid"
        )

    # Get the event type from the headers.
    event_type = request.headers.get("X-GitHub-Event", "ping")

    # Handle the 'ping' event to confirm the webhook is active.
    if event_type == "ping":
        return {"msg": "Ping event received successfully!"}

    # Parse the request body as JSON.
    payload = await request.json()
    action = payload.get("action")
    issue_id = payload.get("issue", {}).get("number")
    repo_name = payload.get("repository", {}).get("full_name")

    # The most important part: checking for the trigger label
    if event_type == "issues" and action == "labeled":
        # labeled_issue = payload.get("issue", {})
        label = payload.get("label", {}).get("name")
        if label == CODING_TRIGGER_LABEL:
            print(f"Label '{CODING_TRIGGER_LABEL}' added to issue #{issue_id}. Dispatching coding agent workflow.")
            run_workflow_dispatch(repo_name=repo_name, issue_id=issue_id)
            return {"msg": f"Dispatched coding agent for issue #{issue_id}."}

    # If the event is a new issue or comment, let the agent decide what to do
    # and use the old logic.
    if event_type in ["issues", "issue_comment"]:
        if action == "opened" or (
            action == "created"
            and payload.get("comment", {}).get("user", {}).get("login")
            != bunsen.agent_name
        ):
            print(f"Received {event_type} event: {action}")
            bunsen.run(repo_name, issue_id)

    return {"msg": "Event processed successfully."}


if __name__ == "__main__":

    # Run the application with Uvicorn.

    # The host is set to "0.0.0.0" to make it accessible from outside the container,
    #   which is necessary for the GitHub webhook to reach it.
    uvicorn.run(app, host="0.0.0.0", port=8000)
