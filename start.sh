#!/bin/bash

# Function to stop all background processes on script exit
cleanup() {
    echo "Stopping all processes..."
    kill $(jobs -p)
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# Start the FastAPI backend
echo "Starting FastAPI backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait a bit to ensure the backend has started
echo "Waiting for backend to start..."
sleep 5

# Start the SvelteKit frontend
echo "Starting SvelteKit frontend..."
cd frontend
npm run preview &

# Wait for all background processes to finish
wait