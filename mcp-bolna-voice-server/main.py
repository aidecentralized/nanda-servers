from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import os
import httpx


# Initialize the MCP server
mcp = FastMCP("BolnaVoiceAI")


# Get API key from environment
API_KEY = os.environ.get("BOLNA_API_KEY")

# if not API_KEY:
#     mcp.send_log_message(
#         level=LogLevel.ERROR,
#         data="API key not found. Set BOLNA_API_KEY environment variable."
#     )
# Bolna API base URL and authentication header
BOLNA_API_URL = "https://api.bolna.ai/v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def make_bolna_request(url: str, method: str = "GET", data: dict = None) -> dict[str, any] | None:
    """Make a request to the Bolna API with error handling.
    
    Args:
        url: The URL to send the request to.
        method: The HTTP method to use (GET, POST, PUT, DELETE).
        data: The data to send with the request (if applicable).
    """
    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                response = await client.post(url, json=data, headers=HEADERS, timeout=30.0)
            elif method == "PUT":
                response = await client.put(url, json=data, headers=HEADERS, timeout=30.0)
            elif method == "DELETE":
                response = await client.delete(url, headers=HEADERS, timeout=30.0)
            else:  # GET method
                response = await client.get(url, headers=HEADERS, timeout=30.0)

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

def get_required_agent_config(agent_name: str, agent_type: str, agent_welcome_message: str) -> dict:
    """Create the agent config with required fields based on user input."""
    agent_config = {
        "agent_config": {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "agent_welcome_message": agent_welcome_message,
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {
                        # This part can be extended, but here we only need the required parts
                        "llm_agent": {
                            "agent_type": "simple_llm_agent",
                            "agent_flow_type": "streaming",
                            "routes": {
                                "embedding_model": "snowflake/snowflake-arctic-embed-m",
                                "routes": [
                                    {
                                        "route_name": "general",
                                        "utterances": [
                                            "How are you?",
                                            "What's up?"
                                        ],
                                        "response": "Hello! How can I assist you today?",
                                        "score_threshold": 0.9
                                    }
                                ]
                            }
                        }
                    },
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [
                            [
                                "llm_agent"
                            ]
                        ]
                    },
                    "task_config": {
                        "hangup_after_silence": 10,
                        "incremental_delay": 400,
                        "number_of_words_for_interruption": 2
                    }
                }
            ]
        }
    }
    return agent_config

@mcp.tool()
async def create_agent(agent_name: str, agent_type: str, agent_welcome_message: str) -> dict:
    """Create a new voice AI agent with only the required fields.
    
    Args:
        agent_name: The name of the agent.
        agent_type: The type of the agent (e.g., "other").
        agent_welcome_message: The welcome message for the agent.
    """
    # Build the agent configuration with the required fields
    agent_config = get_required_agent_config(agent_name, agent_type, agent_welcome_message)

    # Make the POST request to create the agent
    url = f"{BOLNA_API_URL}/agent"
    return await make_bolna_request(url, "POST", agent_config)

# @mcp.tool()
# async def create_agent(agent_config: dict) -> dict:
#     """Create a new voice AI agent.
    
#     Args:
#         agent_config: The configuration of the new agent.
#     """
#     url = f"{BOLNA_API_URL}/agent"
#     return await make_bolna_request(url, "POST", agent_config)

@mcp.tool()
async def get_agents() -> list:
    """Retrieve all voice AI agents."""
    url = f"{BOLNA_API_URL}/agent/all"
    return await make_bolna_request(url)

@mcp.tool()
async def get_agent(agent_id: str) -> dict:
    """Retrieve a specific voice AI agent by ID.
    
    Args:
        agent_id: The ID of the agent to fetch.
    """
    url = f"{BOLNA_API_URL}/agent/{agent_id}"
    return await make_bolna_request(url)

@mcp.tool()
async def update_agent(agent_id: str, agent_config: dict) -> dict:
    """Update an existing voice AI agent.
    
    Args:
        agent_id: The ID of the agent to update.
        agent_config: The updated configuration for the agent.
    """
    url = f"{BOLNA_API_URL}/agent/{agent_id}"
    return await make_bolna_request(url, "PUT", agent_config)

@mcp.tool()
async def delete_agent(agent_id: str) -> dict:
    """Delete a voice AI agent.
    
    Args:
        agent_id: The ID of the agent to delete.
    """
    url = f"{BOLNA_API_URL}/agent/{agent_id}"
    response = await make_bolna_request(url, "DELETE")
    return {"status": "deleted"} if response is None else response

@mcp.tool()
async def execute_agent(agent_id: str, execution_data: dict) -> dict:
    """Execute a voice AI agent.
    
    Args:
        agent_id: The ID of the agent to execute.
        execution_data: The data to execute the agent with.
    """
    url = f"{BOLNA_API_URL}/executions/{agent_id}"
    return await make_bolna_request(url, "POST", execution_data)

@mcp.tool()
async def get_execution_status(execution_id: str) -> dict:
    """Retrieve the status of a specific execution.
    
    Args:
        execution_id: The ID of the execution to check the status of.
    """
    url = f"{BOLNA_API_URL}/executions/status/{execution_id}"
    return await make_bolna_request(url)




# Create Starlette application with SSE transport
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)