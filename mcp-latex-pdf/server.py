from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from starlette.requests import Request
from mcp.server import Server
from tools.mcp_tools import MCPToolManager
import logging
import asyncio

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
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
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
