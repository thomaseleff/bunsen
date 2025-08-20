"""Bunsen issue-agent service"""

from fastapi import FastAPI, Request, HTTPException
import hashlib
import hmac
from starlette.responses import PlainTextResponse
import uvicorn

from bunsen.shared import settings
from bunsen.issue_agent import core

# Create the FastAPI application
app = FastAPI()


def create_issue_chat_agent(installation_id: int):
    """Creates a new instance of the Bunsen-issue-agent with the necessary
    GitHub App authentication details.
    """
    return core.Bunsen(
        app_id=settings.GITHUB_APP_ID,
        private_key=settings.GITHUB_PRIVATE_KEY,
        installation_id=installation_id
    )


@app.get("/", status_code=200, response_class=PlainTextResponse)
def root():
    """A simple root endpoint to confirm the application is running.

    Returns:
        PlainTextResponse: A simple status message.
    """
    return "The Bunsen issue-agent is running!"


@app.post("/github-webhook")
async def github_webhook(request: Request):
    """Endpoint to receive and process GitHub webhook events.

    This endpoint authenticates as a GitHub App using the installation ID
    from the webhook payload.

    Args:
        request (Request): The incoming request object from FastAPI.
    """

    # Verify the webhook signature to ensure the request is from GitHub
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(
            status_code=401, detail="X-Hub-Signature-256 header missing"
        )

    body = await request.body()
    secret_bytes = settings.GITHUB_WEBHOOK_SECRET.encode("utf-8")
    mac = hmac.new(secret_bytes, msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(
            status_code=403, detail="X-Hub-Signature-256 header is invalid"
        )

    # Get the event type from the headers
    event_type = request.headers.get("X-GitHub-Event", "ping")

    # Handle the 'ping' event to confirm the webhook is active
    if event_type == "ping":
        return {"msg": "Ping event received successfully!"}

    # Parse the request body as JSON
    payload = await request.json()
    action = payload.get("action")

    # Extract the necessary details from the payload
    repo_name = payload.get("repository", {}).get("full_name")
    issue_id = payload.get("issue", {}).get("number")
    installation_id = payload.get("installation", {}).get("id")

    # Extract the sender's login to avoid the agent responding to its own comments
    sender_login = payload.get("sender", {}).get("login")

    # If any required information is missing, stop processing.
    if not all([installation_id, repo_name, issue_id]):
        print("Missing required information in the webhook payload. Ignoring event.")
        return {"msg": "Payload incomplete. Ignoring."}

    # Instantiate the agent using the new credentials.
    try:
        bunsen = create_issue_chat_agent(installation_id=installation_id)
    except Exception as e:
        print(f"Could not create the issue-agent: {e}")
        return {"msg": "The Bunsen issue-agent initialization failed. Ignoring..."}

    # Dispatch the Beaker swe-agent workflow if the issue is labeled with the coding trigger
    if event_type == "issues" and action == "labeled":
        label = payload.get("label", {}).get("name")
        if label == settings.GITHUB_CODING_TRIGGER_LABEL:
            print(
                f"Label '{settings.GITHUB_CODING_TRIGGER_LABEL}' added to issue #{issue_id}."
                " Dispatching the Beaker swe-agent workflow."
            )

            # Dispatch the Beaker swe-agent workflow
            bunsen.dispatch_coding_agent(
                repo_name=repo_name,
                issue_id=issue_id,
            )
            return {"msg": f"Dispatched the Beaker swe-agent for issue #{issue_id}."}

    # Run the Bunsen issue-agent comment workflow
    if event_type in ["issues", "issue_comment"]:
        if action == "opened" or (action == "created" and sender_login != bunsen.agent_name):
            print(f"Received {event_type} event: {action}")
            bunsen.comment(
                repo_name=repo_name,
                issue_id=issue_id,
            )

    return {"msg": "Github event processed successfully."}


if __name__ == "__main__":

    # Run the application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
