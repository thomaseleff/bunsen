# 🧪 Bunsen -- Your AI Research & Development Duo

Welcome to **Bunsen**, your experimental (and occasionally explosive) AI-powered duo for streamlined software development\! Inspired by the brilliant, yet sometimes oblivious, Dr. Bunsen Honeydew and his long-suffering, accident-prone assistant, Beaker, our agents aim to accelerate your development cycles while keeping you safe from unexpected "meep meep\!" moments.

At Bunsen Labs, Dr. Bunsen (**Issue-Chat Agent**) meticulously researches and clarifies requirements, ensuring the blueprints are sound. Meanwhile, Beaker (**Coding Agent**, powered by the Mini-SWE agent) bravely takes those plans and builds, tests, and deploys the code. We all know Beaker can be a bit... unpredictable, so we've built a crucial **human-in-the-loop** safety mechanism to prevent those infamous lab "explosions." 💥

## 🚀 The Bunsen Dynamic -- Features & Philosophy

Bunsen isn't just about throwing AI at your codebase. It's about intelligent collaboration:

  * **Dr. Bunsen (The Requirements Clarifier)**: Our Issue-Chat Agent acts as your AI product manager or business analyst.
      * **Interactive Issue Discussions**: Chat directly within GitHub issues to refine requirements, clarify design choices, and define precise success criteria. Dr. Bunsen will ask probing questions, reference existing code, and ensure every detail is meticulously documented before Beaker even touches a keyboard.
      * **Contextual Understanding**: Dr. Bunsen has read-access to your repository. This means it can review existing code, documentation, and project structure to provide informed suggestions and catch potential conflicts early. No more vague requirements leading to rework\!
  * **Beaker (The Autonomous Coder & Tester)**: Our Coding Agent, built upon the efficient Mini-SWE agent, takes clear instructions and gets to work.
      * **Autonomous Implementation**: Once Dr. Bunsen has finalized the requirements, Beaker autonomously implements, tests, and commits code changes.
      * **Automated PR Generation**: Beaker will open a new pull request, linking back to the original issue, and assign you as the reviewer.
      * **Test-Driven Execution**: Beaker is trained to run tests and ensure the code changes meet the defined success criteria, reducing the chances of broken builds.
  * **The Human-in-the-Loop: Preventing Explosions\!** 🧑‍💻
      * We understand that even the most brilliant experiments can go awry. That's why you, the human, are always in control.
      * **Review Before Merge**: Every change Beaker makes results in a pull request. You get to review the code, suggest changes, and ensure it aligns with your vision before it's merged into your main branch. This prevents unexpected "meep-meep" bugs from making it into production.
      * **Iterative Feedback**: If Beaker's PR isn't quite right, simply add comments on the pull request. Beaker can then iterate on the changes based on your feedback, just like a human collaborator.

With Bunsen, you get the speed and scalability of AI development combined with the critical oversight of human intelligence, ensuring your projects progress rapidly and safely.

-----

# 🔬 The Inner Workings of Bunsen

Behind the scenes, Bunsen's magic happens through a combination of configuration files, a publicly exposed webhook, and powerful GitHub Actions workflows.

## Agent Configuration

Bunsen's behavior is managed by two distinct configuration files:

  * `settings.yaml`: This file contains non-sensitive settings that can be safely committed to your repository. It defines the agent personas, the GitHub trigger label (`ready-for-dev`), and the specific LLM models used by each agent (`gemini-1.5-pro` for Bunsen and `gemini-1.5-flash` for Beaker).
  * `.env`: This file contains all your sensitive secrets, such as your **GitHub token** and **LLM API key**. It is crucial to never commit this file to version control.

## How the Agents Interact

The interaction between the user, Bunsen, and Beaker is a carefully orchestrated sequence of events:

  1. A user creates a GitHub issue or adds a comment.
  2. GitHub sends a webhook payload to your deployed `issue_chat_agent` (a FastAPI application).
  3. The `issue_chat_agent` processes this payload. If it detects the ready-for-dev label, it initiates the next phase.
  4. The `issue_chat_agent` makes a GitHub API call to trigger the `swe_agent.yaml` GitHub Actions workflow, passing the issue ID as a parameter.
  5. A GitHub runner starts a job, clones the repository, and executes the Python script for the coding_agent.
  6. The `coding_agent` gets to work, generating code and creating a pull request for human review.

## Deployment

Deploying the Bunsen system involves two main components:

  * **Issue Agent** (`bunsen/issue_chat_agent/agent.py`): This is a FastAPI application that must be hosted on a public server (like a cloud VM or container platform) so GitHub's webhook can reach it.
  * **Coding Agent** (`bunsen/coding_agent/agent.py`): This agent runs directly on GitHub's own infrastructure via GitHub Actions. It does not require separate hosting. Your workflow file (`swe_agent.yaml`) tells GitHub how to set up the environment and run the agent.

----

## 🌟 Getting Started

To integrate Bunsen into your workflow, you'll primarily interact with GitHub issues and pull requests.

### Prerequisites

  * **Python 3.11+**: Ensure you have a compatible Python environment.
  * **GitHub Account**: You'll need a GitHub account and admin access to the repositories you wish to integrate with.
  * **GitHub App or Personal Access Token (PAT)**: For authentication with the GitHub API. GitHub Apps are recommended for production environments.
  * **LLM API Key**: An API key for your chosen Large Language Model (e.g., OpenAI, Anthropic, Google Gemini).

### Installation

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/your-username/bunsen.git
    cd bunsen
    ```

2.  **Create a Virtual Environment** (Recommended):

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Copy the example environment file and fill in your secrets. **Do not commit your `.env` file to version control\!**

    ```bash
    cp .env.example .env
    # Open .env and add your GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET, LLM_API_KEY, etc.
    ```

5.  **Set up GitHub Webhooks**:
    Configure a webhook in your GitHub repository settings to point to your deployed `issue_chat_agent`'s `app.py` endpoint (e.g., `https://your-server.com/github-webhook`). Ensure you select the `Issues` and `Issue comments` events.

6.  **Set up GitHub Actions Workflows**:
    Ensure the `issue_chat_webhook.yml` and `coding_agent_trigger.yml` workflows in `.github/workflows/` are correctly configured for your deployment. These workflows will manage the triggering of your agents based on GitHub events.

-----

## 👩‍🔬 Usage -- How to Work with Bunsen

### Dr. Bunsen (Issue-Chat Agent)

1.  **Create a New GitHub Issue**: Describe the feature, bug, or task you want to address.
2.  **Tag Dr. Bunsen**: In an issue comment, mention `@your-bot-username` (replace `your-bot-username` with the actual username of your GitHub App or bot user).
      * **Example**: "Hey `@your-bot-username`, I need to add a new user profile page. What information should it display, and what are the security considerations?"
3.  **Iterate on Requirements**: Dr. Bunsen will respond in the issue comments, asking clarifying questions, suggesting design elements, and refining success criteria. Continue the conversation until the requirements are crystal clear.
4.  **Signal for Beaker**: Once you're satisfied with the requirements, add a specific label (e.g., `ready-for-dev` or `bunsen-ready`) to the issue. This tells Dr. Bunsen that the task is now prepared for Beaker.

### Beaker (Coding Agent)

1.  **Trigger Implementation**: When the `ready-for-dev` (or configured) label is added to an issue, a GitHub Action workflow will automatically trigger Beaker (the `coding_agent/runner.py`).
2.  **Autonomous Development**: Beaker will:
      * Read the issue and its clarified requirements.
      * Work in a sandboxed environment to implement the code changes.
      * Run tests to ensure functionality.
      * Commit the changes to a new branch (e.g., `feat/issue-123-new-profile-page`).
3.  **Pull Request for Review**: Beaker will automatically open a pull request assigned to you for review.
4.  **Review and Iterate**:
      * Review Beaker's code changes.
      * If changes are needed, add comments directly on the pull request. Beaker can attempt to address these comments and push new commits to the PR.
      * Once satisfied, merge the pull request\!

-----

## 🤯 Preventing Explosions -- Best Practices

While Bunsen and Beaker are diligent, AI can sometimes have unexpected results (just like in the lab\!). Follow these best practices to ensure a smooth, explosion-free workflow:

  * **Start Small**: Begin with simpler issues and features to get comfortable with the agents' behavior.
  * **Clear & Concise Issues**: The clearer your initial issue description, the better Dr. Bunsen can guide the conversation and prepare Beaker.
  * **Thorough Review**: Always carefully review Beaker's generated pull requests. Think of it as a final safety check before the experiment goes live.
  * **Provide Detailed Feedback**: If Beaker makes a mistake, provide clear and specific feedback in the PR comments. The more precise you are, the better Beaker can learn and adapt.
  * **Monitor Workflows**: Keep an eye on your GitHub Actions workflows for any failures or unexpected behavior.

-----
