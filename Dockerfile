# Bunsen Issue Chat Agent
FROM python:3.12-slim

WORKDIR /bunsen

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /bunsen

# Install Python dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "-m", "bunsen.issue_chat_agent.agent"]
