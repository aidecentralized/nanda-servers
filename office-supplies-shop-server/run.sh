#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "================ Starting Run Phase ================"

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log_message "ERROR: Run failed at line $1"
    exit 1
}

# Function to handle SIGTERM gracefully
handle_sigterm() {
    log_message "Received SIGTERM signal, shutting down gracefully..."
    # Send SIGTERM to the child process (Python server)
    if [ -n "$server_pid" ]; then
        kill -TERM "$server_pid" 2>/dev/null || true
    fi
    log_message "Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap 'handle_error $LINENO' ERR
trap 'handle_sigterm' SIGTERM SIGINT

# Set environment variables with defaults
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8080"}
export PYTHONUNBUFFERED="1"
export LOG_LEVEL=${LOG_LEVEL:-"info"}

# Activate virtual environment
log_message "Activating virtual environment"
if [ -d "venv" ]; then
    . venv/bin/activate
else
    log_message "ERROR: Virtual environment not found!"
    exit 1
fi

# Verify server.py exists
if [ ! -f server.py ]; then
    log_message "ERROR: server.py not found!"
    exit 1
fi

# Verify inventory.csv exists
if [ ! -f inventory.csv ]; then
    log_message "ERROR: inventory.csv not found!"
    exit 1
fi

# Run application health check in the background
log_message "Starting health check endpoint on port 8081"
python3 health_check.py &
health_check_pid=$!

# Log some information before starting the server
log_message "Starting Inventory MCP Server on $HOST:$PORT"
log_message "Python version: $(python3 --version)"
log_message "Current directory: $(pwd)"
log_message "Files in current directory: $(ls -la)"

# Start the main application
log_message "Starting main application"
python3 server.py --host $HOST --port $PORT &
server_pid=$!

# Wait for both processes, restart if they exit unexpectedly
log_message "Server started with PID: $server_pid"
log_message "Health check service started with PID: $health_check_pid"
log_message "================ Run Phase Initialized ================"

# Function to restart a process if it fails
restart_if_needed() {
    local pid=$1
    local name=$2
    local cmd=$3
    
    if ! kill -0 $pid 2>/dev/null; then
        log_message "WARNING: $name (PID: $pid) has stopped. Restarting..."
        eval "$cmd" &
        return $!
    fi
    return $pid
}

# Main process monitoring loop
while true; do
    # Check main server
    if ! kill -0 $server_pid 2>/dev/null; then
        log_message "WARNING: Main server (PID: $server_pid) has stopped. Restarting..."
        python3 server.py --host $HOST --port $PORT &
        server_pid=$!
        log_message "Main server restarted with PID: $server_pid"
    fi
    
    # Check health check service
    if ! kill -0 $health_check_pid 2>/dev/null; then
        log_message "WARNING: Health check service (PID: $health_check_pid) has stopped. Restarting..."
        python3 health_check.py &
        health_check_pid=$!
        log_message "Health check service restarted with PID: $health_check_pid"
    fi
    
    # Sleep to avoid busy waiting
    sleep 5
done

