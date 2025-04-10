# BolnaVoiceAI MCP Server with FastMCP

This repository provides a Python-based **MCP (Model Context Protocol)** server that integrates with **Bolna AI**'s API to handle voice agents and initiate voice calls. The server is built using **FastMCP** and **httpx** for asynchronous operations. It includes tools for creating, retrieving, updating, deleting, and executing voice AI agents from Bolna.

Additionally, this repository includes instructions on how to integrate the MCP server with **Claude Desktop** by configuring a JSON file.

## Features

- **Create, retrieve, update, and delete agents** using the Bolna API.
- **Execute agent actions** with the `/executions/{agent_id}` endpoint.
- **FastMCP** server with easy-to-integrate tools.
- **Asynchronous HTTP requests** via `httpx` to efficiently handle API calls.

## Prerequisites

- Python 3.7 or higher
- Install the required dependencies:
  ```bash
    # Install uv
      curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **Bolna API Key**: You will need an API key from the [Bolna AI platform](https://platform.bolna.ai) to authenticate API requests.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repository/BolnaVoiceAI-MCP.git
cd BolnaVoiceAI-MCP
```

### 2. Install Dependencies

```bash
    # Create virtual environment and activate it
        uv venv
        source .venv/bin/activate
        uv add "mcp[cli]" httpx
```

### 3. Configure Your Bolna API Key

In the `bolna_mcp_server.py` file, set the **API key** for authenticating with the Bolna API:

```python
API_KEY = "your_bolna_api_key"  # Replace with your actual Bolna API key
```

### 4. Run the MCP Server

Once everything is set up, you can run the server:

```bash
uv run bolna.py
```

The server will start and expose the following tools for interaction:
- `/agent/create` (POST)
- `/agent/all` (GET)
- `/agent/{agent_id}` (GET)
- `/agent/{agent_id}` (PUT)
- `/agent/{agent_id}` (DELETE)
- `/executions/{agent_id}` (POST)
- `/executions/status/{execution_id}` (GET)


## Tools in the MCP Server

### 1. **create_agent**
Create a new voice AI agent.

**Endpoint**: `/agent/create` (POST)

```json
{
  "name": "Agent Name",
  "description": "Agent Description"
}
```

### 2. **get_agents**
Retrieve all voice AI agents.

**Endpoint**: `/agent/all` (GET)

### 3. **get_agent**
Retrieve a specific voice AI agent by ID.

**Endpoint**: `/agent/{agent_id}` (GET)

### 4. **update_agent**
Update an existing voice AI agent.

**Endpoint**: `/agent/{agent_id}` (PUT)

```json
{
  "name": "Updated Agent Name",
  "description": "Updated Agent Description"
}
```

### 5. **delete_agent**
Delete a voice AI agent by ID.

**Endpoint**: `/agent/{agent_id}` (DELETE)

### 6. **execute_agent**
Execute a specific agent with execution data.

**Endpoint**: `/executions/{agent_id}` (POST)

```json
{
  "data": "execution data"
}
```

### 7. **get_execution_status**
Retrieve the status of an execution by its ID.

**Endpoint**: `/executions/status/{execution_id}` (GET)


---

## Integrating with **Claude Desktop**

To integrate this MCP server with **Claude Desktop**, you need to configure a JSON file that allows Claude to communicate with the MCP server.

### 1. **Configuration File (`claude_config.json`)**

Create a `claude_config.json` file with the following structure:

```json

{
  "mcpServers": {
      "bolna": {
          "command": "uv",
          "args": [
              "--directory",
              "/Users/admin/Documents/bolna",
              "run",
              "bolna.py"
          ]
      }
  }
}
```

**Explanation of Fields**:
- **`claude_mcp_server`**: The URL where your MCP server is running (default is `http://localhost:8000`).
- **`api_key`**: Your Bolna API key to authenticate requests.
- **`agent_id`**: The ID of the voice AI agent you want to interact with.
- **`phone_number`**: The phone number that will be used for the call.
- **`call_message`**: A message to be played when the call is made.

### 2. **Using the Configuration in Claude Desktop**

Once the `claude_config.json` file is ready, you can configure **Claude Desktop** to use the MCP server by reading this configuration file. Make sure that Claude is able to access the MCP server, either locally or over the network.

- **Configure Claude Desktop** to call the MCP server's `make_call` tool using the settings defined in `claude_config.json`.
- Claude Desktop will send the call request with the appropriate data, and the MCP server will initiate the call using Bolna's API.

---

## Troubleshooting

### 1. **Error Handling**

Ensure that you have set up proper error handling for HTTP requests in the MCP server. This includes catching any exceptions when making requests to Bolna's API.

### 2. **Authentication**

If you encounter authentication issues, make sure that your API key is valid and has the correct permissions to access the relevant Bolna API endpoints.

### 3. **Firewall/Network Issues**

If you're unable to connect to the MCP server from Claude Desktop, ensure that the MCP server is running and accessible. If necessary, adjust firewall or network settings to allow communication between Claude and the server.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

---

## Conclusion

This **BolnaVoiceAI MCP Server** provides a robust interface for managing Bolna AI's voice agents and initiating voice calls. By using **FastMCP** and **httpx**, it ensures efficient, asynchronous communication with Bolna's APIs. The integration with **Claude Desktop** via a configurable JSON file allows you to easily automate voice calls and agent interactions.
