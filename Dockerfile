# Use an official Node.js runtime as a parent image
FROM node:18-slim

# Install Python and other dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    ffmpeg \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the backend requirements file and install Python dependencies
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip3 install --no-cache-dir --upgrade pip setuptools

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt --use-pep517

# Copy the frontend package.json and package-lock.json
COPY frontend/package*.json /app/frontend/

# Install frontend dependencies
WORKDIR /app/frontend
RUN npm ci

# Copy the rest of the application code
COPY . /app

# Set up Svelte Kit and build the frontend
WORKDIR /app/frontend
RUN npx svelte-kit sync
RUN npm run build

# After building the frontend
RUN ls -la /app/frontend/build

# Set the working directory back to the root
WORKDIR /app

# Expose the application ports
EXPOSE 8000 5173

# Copy the start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Command to run both backend and frontend
CMD ["/app/start.sh"]