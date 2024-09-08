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
uvicorn main:app --reload &

# Wait a bit to ensure the backend has started
sleep 5

# Start the SvelteKit frontend
echo "Starting SvelteKit frontend..."
cd frontend
npm run dev &

# Wait for all background processes to finish
wait