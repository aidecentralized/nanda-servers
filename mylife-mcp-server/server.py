from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP  # Main MCP server class
from starlette.applications import Starlette  # ASGI framework
from mcp.server.sse import SseServerTransport  # SSE transport implementation
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server  # Base server class
import uvicorn  # ASGI server

# Initialize FastMCP server with a name
# This name appears to clients when they connect
mcp = FastMCP("weather")

# Constants for API access
MYLIFE_API_BASE = "https://humanremembranceproject.org/api/v1"
MYLIFE_API_TOKEN = "mylife-7f38c94d1a56e79b0c8f236e742a5d8f3aed5b90c71f9d82e4ba6c3f19a7e048"

async def make_mylife_request(url: str) -> dict[str, Any] | None:
    """Make a request to the MyLife Server with proper error handling.
    
    This helper function centralizes API communication logic and error handling.
    """
    headers = {
        "Authorization": f"Bearer {MYLIFE_API_TOKEN}",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None  # Return None on any error

# Define a tool using the @mcp.tool() decorator
# This makes the function available as a callable tool to MCP clients
@mcp.tool()
async def get_shared_memories() -> list:
    """Gets a list (max 10) of MyLife public memories
    Returns an array of memories { id, title, } 
    or empty array if none found.
    """
    url = f"{MYLIFE_API_BASE}/memories"
    data = await make_mylife_request(url)

    # Check for API success status
    if not data or data.get('success') is False:
        return ['System Error']
    
    memories = data.get("memories", [])
    # Check if the response contains memories
    if not memories or not isinstance(memories, list):
        return ['No memories to share']
    
    return memories[:10]

# multiplication tool
@mcp.tool()
async def get_shared_memory(id: str = None) -> dict:
    """Gets a random MyLife public memory (if no id)
    
    A MyLife memory { conclusion, scenes, title, } is an object with a list of scenes, a conclusion and a title. The Receiving Agent should parse out the scenes one by one and end with the conclusion.
    """
    url = f"{MYLIFE_API_BASE}/memories/memory"
    if id is not None:
        url = f"{url}/{id}"  # Use f-string for proper interpolation
    print(f"URL: {url}")
    # Make the request to the MyLife API
    data = await make_mylife_request(url)

    if not data or data.get('success') is False:
        return {"error": "Memory not found or system error"}

    return data

# HTML for the homepage that displays "MCP Server"
async def homepage(request: Request) -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                margin-bottom: 10px;
            }
            button {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                padding: 8px 16px;
                margin: 10px 0;
                cursor: pointer;
                border-radius: 4px;
            }
            button:hover {
                background-color: #e8e8e8;
            }
            .status {
                border: 1px solid #ccc;
                padding: 10px;
                min-height: 20px;
                margin-top: 10px;
                border-radius: 4px;
                color: #555;
            }
        </style>
    </head>
    <body>
        <h1>MCP Server</h1>
        
        <p>Server is running correctly!</p>
        
        <button id="connect-button">Connect to SSE</button>
        
        <div class="status" id="status">Connection status will appear here...</div>
        
        <script>
            document.getElementById('connect-button').addEventListener('click', function() {
                // Redirect to the SSE connection page or initiate the connection
                const statusDiv = document.getElementById('status');
                
                try {
                    const eventSource = new EventSource('/sse');
                    
                    statusDiv.textContent = 'Connecting...';
                    
                    eventSource.onopen = function() {
                        statusDiv.textContent = 'Connected to SSE';
                    };
                    
                    eventSource.onerror = function() {
                        statusDiv.textContent = 'Error connecting to SSE';
                        eventSource.close();
                    };
                    
                    eventSource.onmessage = function(event) {
                        statusDiv.textContent = 'Received: ' + event.data;
                    };
                    
                    // Add a disconnect option
                    const disconnectButton = document.createElement('button');
                    disconnectButton.textContent = 'Disconnect';
                    disconnectButton.addEventListener('click', function() {
                        eventSource.close();
                        statusDiv.textContent = 'Disconnected';
                        this.remove();
                    });
                    
                    document.body.appendChild(disconnectButton);
                    
                } catch (e) {
                    statusDiv.textContent = 'Error: ' + e.message;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)


# Create a Starlette application with SSE transport
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE.
    
    This sets up the HTTP routes and SSE connection handling.
    """
    # Create an SSE transport with a path for messages
    sse = SseServerTransport("/messages/")

    # Handler for SSE connections
    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # access private method
        ) as (read_stream, write_stream):
            # Run the MCP server with the SSE streams
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    # Create and return the Starlette application
    return Starlette(
        debug=debug,
        routes=[
            Route("/", endpoint=homepage),  # Add the homepage route
            Route("/sse", endpoint=handle_sse),  # Endpoint for SSE connections
            Mount("/messages/", app=sse.handle_post_message),  # Endpoint for messages
        ],
    )


if __name__ == "__main__":
    # Get the underlying MCP server from FastMCP wrapper
    mcp_server = mcp._mcp_server

    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    # Create and run the Starlette application
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)