# bunsen -- an AI research & development squad

Welcome to 🧪 `bunsen`, an experimental (and occasionally explosive) AI-powered squad for software development\! Inspired by the brilliant, yet sometimes oblivious, Dr. Bunsen Honeydew and his long-suffering, accident-prone assistant, Beaker, from the Muppets. Bunsen and Beaker work together to accelerate your development cycles while keeping you safe from unexpected "meep meep\!" moments.

Bunsen (the **issue-agent**) meticulously researches and clarifies requirements, ensuring the implementation details are sound. Meanwhile, Beaker (the **swe-agent**) bravely takes those plans and builds, tests, and deploys the code. Beaker can be a bit... unpredictable, so the entire workflow maintains a crucial **human-in-the-loop** safety mechanism to prevent those infamous lab 💥 "explosions".

## The bunsen dynamic -- features & philosophy

🧪 `bunsen` isn't just about throwing AI at your codebase. It's about intelligent collaboration,

  * **Bunsen** acts as your AI product manager / business analyst, expanding your Github experience with **Interactive issue discussions** and **Contextual understanding**.
      * **Interactive issue discussions** Chat directly with Bunsen in GitHub issues to refine requirements, clarify design choices, and define precise success criteria. Bunsen will ask probing questions, and ensure every detail is meticulously documented before Beaker even touches a keyboard.
      * `coming-soon` **Contextual understanding** Bunsen has read-access to your repository. This means it can review existing code, documentation, and project structure to provide informed suggestions and catch potential conflicts early. No more vague requirements leading to rework\!
  * **Beaker** acts as your AI software engineer, expanding your product development squad with an embedded engineer within Github Actions providing **Autonomous implementation**, **Automated pr generation**, and **Test-driven execution**.
      * **Autonomous implementation** Once Bunsen has finalized the requirements, Beaker autonomously implements, tests, and commits code changes.
      * **Automated pr generation** Beaker will open a new pull request, linking back to the original issue, and assign you as the reviewer.
      * **Test-driven execution** Beaker is trained to run tests and ensure the code changes meet the defined success criteria, reducing the chances of broken builds.
  * **Human-in-the-loop**
      * Even the most brilliant experiments can go awry. That's why you, the human, are always in control.
      * **Review-before-you-merge** Every change Beaker makes results in a pull request. You get to review the code, suggest changes, and ensure it aligns with your vision before it's merged into your main branch.
      * `coming-soon` **Iterative feedback** If Beaker's PR isn't quite right, simply add comments on the pull request. Beaker can then iterate on the changes based on your feedback, just like a human collaborator.

🧪 `bunsen` provides the speed and scalability of AI development combined with the critical oversight of human intelligence, ensuring your project progresses rapidly and safely.

-----

# How bunsen works

Behind the scenes, Bunsen's magic happens through a combination of configuration files, a publicly exposed webhook, and a GitHub Actions workflow.

## Agent configuration

Bunsen and Beaker's behavior is managed by two distinct configuration files:

  * `settings.yaml` Contains non-sensitive settings that can be safely committed to your repository. It defines the GitHub repository details (e.g. the coding trigger label (`ready-for-dev`)), and the specific LLM models used by each agent (e.g. `openai/gpt-5`). See the LiteLLM [documentation](https://docs.litellm.ai/docs/providers) on available providers.
  * `.env` Contains sensitive secrets, such as the Github App credentials and LLM API Key. Never commit this file to your repository.

## How the agents interact

The interaction between the user, Bunsen, and Beaker is a carefully orchestrated sequence of events,

  1. A user creates a GitHub issue or adds a comment to an existing issue.
  2. GitHub sends a webhook payload via a Github App to your deployed Bunsen `issue_agent` (a FastAPI application).
  3. The Bunsen `issue_agent` processes the payload, responding on the Github issue when mentioned, e.g. `@bunsen-issue-agent`, or dispatching the Beaker `swe-agent` if it detects that the coding trigger label was added to the Github issue.
  4. If the coding trigger label is detected the Bunsen `issue-agent` makes a GitHub API call to trigger the Beaker `swe-agent`, defined within a Github Action workflow (e.g., `.github/workflows/swe_agent.yaml`).
  5. Once dispatched, a GitHub runner starts a job, clones the repository, and executes the Python script for the Beaker `swe-agent`.
  6. Finally, the Beaker `swe-agent` gets to work, generating code and creating a pull request for review.

## Deployment

Deploying 🧪 `bunsen` involves two main components,

  * The Bunsen **issue-agent** (`bunsen/issue_agent/agent.py`) The FastAPI application that must be hosted on a public server (like a cloud VM or container platform) so that it is reachable by a GitHub webhook.
  * The Beaker **swe-agent** (`bunsen/swe_agent/agent.py`) The agent runs directly on GitHub's own infrastructure via GitHub Actions. It does not require separate hosting. A Github Actions workflow file (e.g. `.github/workflows/swe_agent.yaml`) tells GitHub how to set up the environment and run the agent.

----

## Getting started

To integrate 🧪 `bunsen` into your workflow, you'll primarily interact with GitHub issues and pull requests.

### Prerequisites

  * **Python 3.11+**: Ensure you have a compatible Python environment.
  * **GitHub Account**: You'll need a GitHub account and admin access to the repositories you wish to integrate with.
  * **GitHub App**: For authentication with the GitHub API. A Github App also provides your bunsen issue-agent with its persona (e.g. if you name the Github App `bunsen-issue-agent`, you'll mention the agent in issues by including `@bunsen-issue-agent`.)
  * **LLM API key**: An API key for your chosen Large Language Model (e.g., OpenAI, Anthropic, etc.). See the LiteLLM [documentation](https://docs.litellm.ai/docs/providers) on available providers. Keep in mind that the underlying tools, `swe-agent` and `LiteLLM` are in-development and some providers may not perform as well as others. Check the Github repositories of each of those projects for up-do-date information on the best supported providers/models.

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/thomaseleff/bunsen.git
    cd bunsen
    ```

2.  **Create a virtual environment**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, .venv\Scripts\activate
    ```

3.  **Install the library**

    ```bash
    pip install .
    ```

4.  **Configure environment variables**
    Copy the example environment file, `.env.example` and fill in your secrets.

    ```bash
    cp .env.example .env
    # Open .env and add your tokens and secrets.
    ```

5.  **Create a Github App and set up GitHub webhooks**
    Create a Github App and configure a webhook to your deployed Bunsen `issue-agent` FastAPI application (e.g., `https://your-server.com/github-webhook`).
    
    Enable `Actions` (as 'Read and write'), `Contents` (as 'Read and write), `Issues` (as 'Read and write'), and `Pull requests` (as Read and write) within the **Repository permissions**.
    
    Subscribe to the `Issues`, `Issue comment`, and `Label` events.

6.  **Set up GitHub Actions workflows**
    Ensure the `swe-agent.yaml` workflows in `.github/workflows/` are correctly configured for your deployment.

-----

## Usage -- how to work with bunsen

### Bunsen (issue-agent)

1.  **Create a new GitHub issue** Describe the feature, bug, or task you want to address.
2.  **Tag Bunsen** In an issue comment, mention `@your-bot-username` (replace `your-bot-username` with the actual name of your GitHub App).
      * **Example** "Hey `@bunsen-issue-agent`, I need to add a new user profile page. What information should it display, and what are the security considerations?"
3.  **Iterate on requirements** Bunsen will respond in the issue comments, asking clarifying questions, suggesting design elements, and refining success criteria. Continue the conversation until the requirements are finalized.
4.  **Tag the issue for development** Once you are satisfied with the requirements, add the coding trigger label (e.g., `ready-for-dev`) to the issue. This tells Bunsen that the task is now prepared for Beaker.

### Beaker (swe-agent)

1.  **Trigger implementation** When the coding trigger label (e.g., `ready-for-dev`) is added to an issue, Bunsen will dispatch Beaker via a Github Action workflow.
2.  **Autonomous development** Beaker will,
      * Read the issue and comments
      * Work in a sandboxed environment to implement code changes
      * Run tests to ensure functionality
      * Commit the changes to a new branch (e.g., `feat/issue-123-new-profile-page`).
3.  **Pull request for review** Beaker will automatically open a pull request assigned to you for review.
4.  **Review and iterate**
      * Review Beaker's code changes.
      * `coming-soon` If changes are needed, add comments directly on the pull request. Beaker can attempt to address these comments and push new commits to the PR.
      * Once satisfied, merge the pull request\!

-----

## Preventing explosions

While Bunsen and Beaker are diligent, AI can sometimes have unexpected results (just like in the lab\!). Follow these best practices to ensure a smooth, explosion-free workflow,

  * **Start small** Begin with simpler issues and features to get comfortable with the agents' behavior.
  * **Clear & concise issues** The clearer your initial issue description, the better Bunsen can guide the conversation and prepare Beaker.
  * **Thorough review**: Always carefully review Beaker's generated pull requests. Think of it as a final safety check before the experiment goes live.
  * `coming-soon` **Provide detailed feedback** If Beaker makes a mistake, provide clear and specific feedback in the PR comments. The more precise you are, the better Beaker can learn and adapt.
  * **Monitor workflows** Keep an eye on your GitHub Actions workflows for any failures or unexpected behavior.
