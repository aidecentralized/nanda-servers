from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.responses import HTMLResponse
from mcp.server import Server
import uvicorn
import httpx

mcp = FastMCP("geo-mcp")

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


# Tool 1: Detect user location from IP
@mcp.tool()
async def get_my_location() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get("https://ipwho.is/")
        return r.json()

# Tool 2: Get current weather
@mcp.tool()
async def get_weather(lat: float, lon: float) -> dict:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json().get("current_weather", {})

# Tool 3: Get time info based on lat/lon
@mcp.tool()
async def get_local_time(lat: float, lon: float) -> dict:
    url = f"http://worldtimeapi.org/api/timezone"
    async with httpx.AsyncClient() as client:
        zones = await client.get(url)
        timezones = zones.json()
        # fallback: return UTC if no matching timezone
        return {"timezone": "UTC", "datetime": "Unknown"}

# Tool 4: Get country info
@mcp.tool()
async def get_country_info(country: str) -> dict:
    url = f"https://restcountries.com/v3.1/name/{country}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
        if isinstance(data, list) and data:
            info = data[0]
            return {
                "name": info.get("name", {}).get("common"),
                "population": info.get("population"),
                "region": info.get("region"),
                "capital": info.get("capital", [None])[0],
                "currency": list(info.get("currencies", {}).keys())[0] if info.get("currencies") else None,
                "languages": list(info.get("languages", {}).values()) if info.get("languages") else []
            }
        return {}

# Tool 5: Geo Summary
@mcp.tool()
async def get_geo_summary() -> dict:
    location = await get_my_location()
    lat = location.get("latitude")
    lon = location.get("longitude")
    country = location.get("country")

    weather = await get_weather(lat, lon)
    time_info = await get_local_time(lat, lon)
    country_info = await get_country_info(country)

    return {
        "location": f"{location.get('city')}, {country}",
        "ip": location.get("ip"),
        "lat": lat,
        "lon": lon,
        "weather": weather,
        "time": time_info,
        "country_info": country_info,
    }

# SSE App
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