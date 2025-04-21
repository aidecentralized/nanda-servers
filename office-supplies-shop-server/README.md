# Office Supplies Inventory NANDA Service using MCP Server + NANDA Registry + NANDA host client

Create a NANDA service using Model Context Protocol (MCP) server code that provides information about office supplies inventory. This service allows AI assistants to query and retrieve information about office supplies using the MCP standard. You will use cloud hosted server and a web based NANDA host client. No need to install a local server.

You can deploy a consumer facing web-app for any standard inventory using the same framework.

## Overview

This project implements a NANDA service using MCP server code that serves office inventory data from a CSV file. It provides tools that allow AI assistants to:
- Get a list of all available items in the inventory
- Retrieve detailed information about specific items by name

## Prerequisites

- Python 3.9 or higher
- Dependencies listed in `requirements.txt`

## Files in this Repository

- `officesupply.py`: The main server implementation
- `inventory.csv`: CSV file containing the office supply inventory data
- `build.sh`: Script for setting up the environment
- `run.sh`: Script for running the server
- `requirements.txt`: List of Python dependencies

## Quick Start

### Local Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/aidecentralized/nanda-servers.git
   cd office-supplies-shop-server
   ```

2. Choose one of the environment setup options below:

#### Option A: Using Python venv

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Option B: Using Conda

1. Create a new conda environment:
   ```bash
   conda create --name inventory_env python=3.11
   ```

2. Activate the conda environment:
   ```bash
   conda activate inventory_env
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server Locally to Test

After setting up your environment using either option above:

1. Run the server:
   ```bash
   python officesupply.py
   ```

2. The server will be available at: http://localhost:8080

### Testing with MCP Inspector

1. Install the MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. Open the URL provided by the inspector in your browser
3. Connect using SSE transport type
4. Enter your server URL with `/sse` at the end (e.g., `http://localhost:8080/sse`)
5. Test the available tools:
   - `get_items`: Lists all item names in the inventory
   - `get_item_info`: Retrieves details about a specific item

## CSV Data Format

The server expects an `inventory.csv` file with at least the following column:
- `item_name`: The name of the inventory item

Additional columns will be included in the item details returned by `get_item_info`.

Within this purview, you can edit the CSV file for your requirements, and the MCP server should work for your CSV file as well.

## Deployment

### Preparing for Cloud Deployment

1. Make sure your repository includes:
   - All code files
   - `requirements.txt`
   - `build.sh` and `run.sh` scripts

2. Set executable permissions on the shell scripts:
   ```bash
   chmod +x build.sh run.sh
   ```

### Deploying to AWS AppRunner

1. Go to AWS AppRunner
2. Create a new service from your source code repository
3. Configure the service:
   - Python 3.11 runtime
   - Build command: `./build.sh`
   - Run command: `./run.sh`
   - Port: 8080

4. Deploy and wait for completion
5. Test the public endpoint with MCP Inspector

### Registering on NANDA Registry

1. Go to [NANDA Registry](https://ui.nanda-registry.com)
2. Login or create an account
3. Click "Register a new server"
4. Fill in the details:
   - Server name
   - Description
   - Public endpoint URL (without `/sse`)
   - Tags and categories
5. Register your server

## Usage in NANDA Host, a Browser based Client

1. Visit [nanda.mit.edu](https://nanda.mit.edu)
2. Go to the NANDA host
3. Add your Anthropic API key
4. Find your MCP server in the registry
5. Add it to your host
6. Test by asking questions that use your server's functionality

## Troubleshooting

- Ensure your CSV file is properly formatted
- Test the server locally before deploying
- Verify your public endpoint works with MCP Inspector before registering
- Check the logs on AWS if deployment fails

## Additional Resources

Check out this video tutorial for a walkthrough of setting up and using the MCP server:
[![MCP Server Tutorial](https://img.youtube.com/vi/i7GPR8LnAWg/0.jpg)](https://www.youtube.com/watch?v=i7GPR8LnAWg)

## Acknowledgments

Based on the [NANDA Servers](https://github.com/aidecentralized/nanda-servers) repository.
Follow ProjectNanda at [https://nanda.mit.edu](https://nanda.mit.edu)


