#!/bin/bash

# Start the backend API server
echo "Starting backend API server..."
cd /workspace
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start the frontend Next.js app
echo "Starting Next.js frontend..."
cd /workspace/client
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Function to kill both processes
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID
    exit
}

# Set up trap to cleanup on exit
trap cleanup EXIT INT TERM

echo "Both servers are running!"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait