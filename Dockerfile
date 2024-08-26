# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any, e.g., build-essential for some packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean

# Upgrade pip and setuptools to avoid potential issues with packages
RUN pip install --upgrade pip setuptools

# Create a virtual environment
RUN python -m venv /app/venv

# Activate the virtual environment and install dependencies
# The `source` command is executed in a single RUN statement to maintain the environment
RUN /bin/bash -c "source /app/venv/bin/activate && pip install --no-cache-dir -r requirements.txt"

# Copy the rest of the application code
COPY . .

# Set environment variables to use the virtual environment by default
ENV PATH="/app/venv/bin:$PATH"

# Expose the application port
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
