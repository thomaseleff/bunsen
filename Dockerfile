# Set the operating-system
FROM python:3.12-slim

# Set the working directory
WORKDIR /bunsen

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/thomaseleff/bunsen.git /bunsen

# Install Python dependencies
RUN python -m pip install --upgrade pip
RUN pip install .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8000

# Run the Bunsen issue-agent
CMD ["python", "-m", "bunsen.issue_agent.agent"]
