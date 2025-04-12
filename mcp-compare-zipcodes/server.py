from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from typing import Any
import httpx
import tempfile
import pandas as pd
from mcp.server.fastmcp import FastMCP
import aiohttp
import asyncio
from scipy.stats import zscore

mcp = FastMCP("my-company-api")

DATA_BASE_URL = "https://web.media.mit.edu/~almurph/censusdata/output_v2/household/"

async def get_state_from_zip(zip_code, api_key):
    url = f"https://api.api-ninjas.com/v1/zipcode?zip={zip_code}"
    headers = {"X-Api-Key": "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        return data[0].get('state', "State not found") if data else "State not found"
                    else:
                        return data.get('state', "State not found")
                else:
                    text = await response.text()
                    return f"Error: {response.status}, {text}"
    except Exception as e:
        return f"Error: {str(e)}"

async def make_request(url: str) -> dict[str, Any] | None:
    """Make a request to the synthetic census data server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
            if url.endswith('.pkl'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                return pd.read_pickle(tmp_path)
            
    except:
        raise Exception("Error fetching data from the server.")


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


@mcp.tool()
async def compare_regions(a: str, b: str) -> str:
    state_a = await get_state_from_zip(a, "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM")
    state_b = await get_state_from_zip(b, "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM")

    df_a = await make_request(f"{DATA_BASE_URL}/{state_a}/{a}_household.pkl")
    df_b = await make_request(f"{DATA_BASE_URL}/{state_b}/{b}_household.pkl")

    if df_a is None or df_b is None:
        return "Error loading data for one or both regions."

    result = []

    group_cols = ['age', 'gender', 'ethnicity']

    agg_a = df_a.groupby(group_cols).size().rename("count_a")
    agg_b = df_b.groupby(group_cols).size().rename("count_b")

    combined = pd.concat([agg_a, agg_b], axis=1).fillna(0)
    combined["z_score"] = zscore(combined["count_a"] - combined["count_b"])

    significant_diffs = combined[combined["z_score"].abs() > 2]
    if not significant_diffs.empty:
        result.append("Significant demographic differences (z > 2):")
        for idx, row in significant_diffs.iterrows():
            result.append(f" - {idx}: z={row['z_score']:.2f}")
    else:
        result.append("No significant demographic differences found.")

    return "\n".join(result)


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
            Route("/", endpoint=homepage),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="localhost", port=8080)