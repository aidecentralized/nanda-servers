from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from starlette.requests import Request
from mcp.server import Server
from tools.mcp_tools import MCPToolManager
import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

#import pypandoc
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
# from pydantic import AnyUrl
import mcp.server.stdio
import os
import docker


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

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


    async def handle_sse(request: Request) -> None:
        try:
            logger.debug("Entering handle_sse")
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
            ) as (read_stream, write_stream):
                request.scope['state'] = {'close_called': False}
                logger.debug("Starting SSE LaTeX MCP server run")
                try:
                    await mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server.create_initialization_options(),
                    )
                except Exception as e:
                    logger.error(f"Error in mcp_server.run: {e}")
                    raise
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in handle_sse: {e}")
            raise
        finally:
            logger.debug("Exiting handle_sse")

    return Starlette(
        debug=debug,
        routes=[
            Route("/", endpoint=homepage),  # Add the homepage route
            Route("/sse", endpoint=handle_sse), # Endpoint for SSE connections
            Mount("/messages/", app=sse.handle_post_message),  # Endpoint for messages
        ],
    )



if __name__ == "__main__":
    import uvicorn

    # Create the tool manager and get the server
    tool_manager = MCPToolManager("LaTeX to PDF")
    mcp_server = tool_manager.server

    # Create the Starlette app
    app = create_starlette_app(mcp_server, debug=True)

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=3004, log_level="debug", timeout_graceful_shutdown=1)
