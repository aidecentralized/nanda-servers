# Building MCP Servers: SSE Implementation Guide

## Table of Contents
- [Introduction](#introduction)
- [What is MCP?](#what-is-mcp)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic SSE Server Architecture](#basic-sse-server-architecture)
- [Step-by-Step Implementation](#step-by-step-implementation)
- [Example Server: Weather API](#example-server-weather-api)
- [Testing Your MCP Server](#testing-your-mcp-server)
- [Advanced Configuration](#advanced-configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Integration with NANDA Client](#integration-with-nanda-client)
- [API Reference](#api-reference)

## Introduction

This guide provides clear documentation for building a Model Context Protocol (MCP) server using Server-Sent Events (SSE) in Python. It's designed for companies that want to expose their APIs to the NANDA client.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol for communication between AI applications (clients) and tools or resources (servers). It enables AI models to access external data and functionality through a well-defined interface.

MCP offers three core primitives:
- **Tools**: Functions the AI model can call
- **Resources**: Data the client application can access
- **Prompts**: Templates for user interaction

## Prerequisites

- Python 3.9+
- Basic understanding of async Python
- Your company's API service or data source
- Knowledge of your API authentication methods

## Installation

```bash
pip install mcp
```

For development installations:

```bash
pip install mcp[dev]
```

## Basic SSE Server Architecture

SSE (Server-Sent Events) provides a persistent HTTP connection for server-to-client messages, ideal for MCP servers that need to maintain state and handle long-running connections.

An MCP SSE server consists of:
1. **FastMCP Server Object**: Manages MCP protocol features
2. **SSE Transport Layer**: Handles HTTP connections
3. **Tool Implementations**: Integrates with your company's API
4. **Web Server**: Typically Starlette/Uvicorn for async support

## Step-by-Step Implementation

### 1. Create a new Python project

```bash
mkdir my-mcp-server
cd my-mcp-server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp httpx uvicorn starlette
```
ALTERNATIVE to the above: you can INSTEAD use an Anaconda environment.
```bash
mkdir my-mcp-server
cd my-mcp-server
conda create -n venv python=3.11
conda activate venv
pip install mcp httpx uvicorn starlette
```

### 2. Set up the basic server structure

Create a file named `server.py`:

```python
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# Initialize FastMCP server
mcp = FastMCP("my-company-api")

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
            Route("/", endpoint=homepage),  # Add the homepage route
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)
```

### 3. Define your tools

Add tool implementations to `server.py`:

```python
import httpx

@mcp.tool()
async def get_company_data(resource_id: str) -> str:
    """Get data from your company API.
    
    Args:
        resource_id: The ID of the resource to fetch
    """
    # Implement your API call here
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.your-company.com/data/{resource_id}",
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        response.raise_for_status()
        return response.text()
```

### 4. Add authentication (if required)

For APIs requiring authentication:

```python
import os
from mcp.server.types import LogLevel

# Get API key from environment
API_KEY = os.environ.get("COMPANY_API_KEY")

if not API_KEY:
    mcp.send_log_message(
        level=LogLevel.ERROR,
        data="API key not found. Set COMPANY_API_KEY environment variable."
    )
```

### 5. Run your server

```bash
python server.py
```

Your MCP server will now be accessible at: `http://localhost:8080` for the web interface and `http://localhost:8080/sse` for the SSE endpoint.

## Example Server: Weather API

Below is a fully annotated implementation of a Weather API MCP server:

```python
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
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"  # Required by NWS API


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling.
    
    This helper function centralizes API communication logic and error handling.
    """
    headers = {
        "User-Agent": USER_AGENT,  # NWS requires a user agent
        "Accept": "application/geo+json"  # Request GeoJSON format
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None  # Return None on any error


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string.
    
    Extracts and formats the most important information from an alert.
    """
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


# Define a tool using the @mcp.tool() decorator
# This makes the function available as a callable tool to MCP clients
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


# Define another tool
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

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
```

## Testing Your MCP Server

### Manual Testing with the MCP Inspector

The MCP Inspector is a command-line tool for testing MCP servers:

```bash
npx @modelcontextprotocol/inspector
```

Connect to your server:

```
> connect sse http://localhost:8080/sse
```

List available tools:

```
> list tools
```

Call a tool:

```
> call get_forecast --latitude 37.7749 --longitude -122.4194
```

## Advanced Configuration

### Adding Resources

Resources provide data to the client application:

```python
@mcp.resource("company-data://{id}")
async def company_data_resource(id: str) -> tuple[str, str]:
    """Provide company data as a resource.
    
    Args:
        id: Resource identifier
        
    Returns:
        Tuple of (content, mime_type)
    """
    # Fetch data from your API
    data = await fetch_company_data(id)
    return data, "application/json"
```

### Adding Prompts

Prompts create templates that users can invoke:

```python
@mcp.prompt()
def data_analysis_prompt(resource_id: str) -> str:
    """Create a prompt for analyzing company data.
    
    Args:
        resource_id: ID of the data to analyze
    """
    return f"""Please analyze the company data with ID {resource_id}.
Focus on key metrics and provide actionable insights."""
```

### Server Lifecycle Management

For more control over server initialization and shutdown:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict]:
    """Manage server startup and shutdown lifecycle."""
    # Initialize resources on startup
    api_client = await setup_api_client()
    try:
        yield {"api_client": api_client}
    finally:
        # Clean up on shutdown
        await api_client.close()

# Create server with lifespan
from mcp.server import Server
server = Server("my-company-api", lifespan=server_lifespan)

# Access context in handlers
@server.call_tool()
async def api_tool(name: str, arguments: dict) -> str:
    ctx = server.request_context
    api_client = ctx.lifespan_context["api_client"]
    return await api_client.request(arguments["endpoint"])
```

## Best Practices

### Error Handling

Implement comprehensive error handling:

```python
@mcp.tool()
async def api_tool(param: str) -> str:
    try:
        # API call here
        return result
    except httpx.RequestError:
        return "Error: Could not connect to the API. Please check your network."
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "Error: Authentication failed. Please check your API key."
        elif e.response.status_code == 404:
            return f"Error: Resource '{param}' not found."
        else:
            return f"Error: HTTP error {e.response.status_code}"
    except Exception as e:
        # Log the full error for debugging
        mcp.send_log_message(level="error", data=f"Unexpected error: {str(e)}")
        return "An unexpected error occurred. Please try again later."
```

### Security Considerations

1. **API Key Management**: Never hardcode API keys; use environment variables
2. **Input Validation**: Validate all inputs before making API calls
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Error Information**: Don't expose sensitive information in error messages

### Performance Optimization

1. **Connection Pooling**: Reuse HTTP connections when possible
2. **Caching**: Cache API responses for frequently requested data
3. **Asynchronous Operations**: Use async for all I/O operations
4. **Timeout Handling**: Set reasonable timeouts for external API calls

## Troubleshooting

### Common Issues and Solutions

1. **Connection Errors**
   - Check network connectivity
   - Verify server is running and accessible
   - Ensure correct host/port configuration

2. **Authentication Failures**
   - Verify API keys are correct
   - Check for expired credentials
   - Ensure proper authorization headers

3. **Timeout Issues**
   - Increase timeout values for long-running operations
   - Optimize API calls for performance
   - Consider implementing request chunking

4. **Protocol Errors**
   - Verify MCP version compatibility
   - Check message format compliance
   - Review server and client logs

### Logging

To enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

To send logs to the MCP client:

```python
@mcp.tool()
async def complex_tool(param: str) -> str:
    mcp.send_log_message(level="info", data=f"Processing request with param: {param}")
    # Process request
    mcp.send_log_message(level="info", data="Request processing complete")
    return result
```

## Integration with NANDA Client:

Connect to the NANDA client through our [web interface](https://main.dayer1hj1pz2p.amplifyapp.com).

<img width="798" alt="image" src="https://github.com/user-attachments/assets/9050e38e-17f2-4b14-b37c-bf4fdcc0f493" />

### Adding a New Server

- Server ID
    - Choose a unique identifier to distinguish your server
- Server Name
    - Set a clear, descriptive name for easy identification
- Server URL
    - Specify the SSE endpoint URL for your NANDA server
<img width="553" alt="image" src="https://github.com/user-attachments/assets/798ea564-268c-47c8-8604-828c7609c269" />


## API Reference

### FastMCP Class

Main class for creating MCP servers:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="my-server",
    description="My API server",
    version="1.0.0"
)
```

### Decorators

- `@mcp.tool()`: Define a function as an MCP tool
- `@mcp.resource(pattern)`: Define a function as an MCP resource
- `@mcp.prompt()`: Define a function as an MCP prompt

### Server Methods

- `mcp.send_log_message(level, data)`: Send log messages to the client
- `mcp.sse_app()`: Create an ASGI app for SSE transport

## Additional Documentation

For more detailed information, refer to:

1. [Model Context Protocol documentation](https://modelcontextprotocol.io/introduction)
2. [Python SDK documentation](https://github.com/modelcontextprotocol/python-sdk)

For questions and community support, email dec-ai@media.mit.edu
