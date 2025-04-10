#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print commands and their arguments as they are executed
set -x

echo "================ Starting Build Phase ================"
BUILD_START_TIME=$(date +%s)

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log_message "ERROR: Build failed at line $1"
    exit 1
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Check if running on Amazon Linux or other distribution and install dependencies
log_message "Installing system dependencies"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "amzn" ]]; then
        # Amazon Linux
        yum update -y
        yum install -y python3-pip python3-devel gcc
    elif [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
        # Ubuntu/Debian
        apt-get update -y
        apt-get install -y python3-pip python3-dev build-essential
    else
        log_message "Unsupported Linux distribution: $ID"
        exit 1
    fi
else
    log_message "Unable to determine OS distribution"
    exit 1
fi

# Verify Python installation
log_message "Verifying Python installation"
python3 --version
python3 -m pip --version

# Upgrade pip
log_message "Upgrading pip"
python3 -m pip install --upgrade pip

# Create virtual environment
log_message "Creating virtual environment"
python3 -m venv venv
. venv/bin/activate

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    log_message "ERROR: requirements.txt not found!"
    exit 1
fi

# Install Python dependencies
log_message "Installing Python dependencies"
pip install --no-cache-dir -r requirements.txt

# Check if server.py exists
if [ ! -f server.py ]; then
    log_message "ERROR: server.py not found!"
    exit 1
fi

# Check if inventory.csv exists
if [ ! -f inventory.csv ]; then
    log_message "ERROR: inventory.csv not found!"
    exit 1
fi

# Set proper file permissions
log_message "Setting file permissions"
chmod 644 inventory.csv
chmod 644 requirements.txt
chmod 755 server.py
chmod 755 run.sh

# Create a simple health check endpoint for AWS App Runner
log_message "Creating health check endpoint"
cat << 'EOF' > health_check.py
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

async def health(request):
    return JSONResponse({"status": "healthy"})

app = Starlette(routes=[
    Route("/health", health),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
EOF

chmod 755 health_check.py

# Create a simple version info file
log_message "Creating version info"
echo "Build completed at: $(date)" > build_info.txt
echo "Python version: $(python3 --version)" >> build_info.txt
echo "Pip version: $(pip --version)" >> build_info.txt

# Calculate and display build time
BUILD_END_TIME=$(date +%s)
BUILD_DURATION=$((BUILD_END_TIME - BUILD_START_TIME))
log_message "Build completed in $BUILD_DURATION seconds"
log_message "================ Build Phase Completed ================"

exit 0

