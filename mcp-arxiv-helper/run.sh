#!/usr/bin/env bash
echo "===== Activating virtual environment ====="
source venv/bin/activate

echo "===== Starting the mcp Server Application ====="
exec python3 main.py --transport sse --host 0.0.0.0 --port 8080