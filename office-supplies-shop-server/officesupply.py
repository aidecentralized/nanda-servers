from typing import Any
import pandas as pd
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# Load the inventory once when the server starts
inventory_df = pd.read_csv("inventory.csv")

# Initialize the MCP server
mcp = FastMCP("inventory")


@mcp.tool()
async def get_items() -> list[str]:
    """Return the list of all item names in the inventory."""
    return inventory_df["item_name"].dropna().unique().tolist()


@mcp.tool()
async def get_item_info(item_name: str) -> dict[str, Any]:
    """Given an item name, return all details of the item."""
    row = inventory_df[inventory_df["item_name"].str.lower() == item_name.lower()]
    if row.empty:
        return {"error": "Item not found."}
    return row.iloc[0].dropna().to_dict()


# HTML homepage
async def homepage(request: Request) -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>MCP Server</title></head>
    <body><h1>Inventory MCP Server</h1><p>Server is running.</p></body>
    </html>
    """
    return HTMLResponse(html_content)


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope, request.receive, request._send
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

    import argparse
    parser = argparse.ArgumentParser(description='Run Inventory MCP server')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
