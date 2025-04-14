from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from datetime import datetime

from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import HTMLResponse
from mcp.server import Server
import uvicorn

mcp = FastMCP("AnyMile")

ANYMILE_URL = "https://api.poc.anymile.io/api/v1/mcp/public"
USER_AGENT = "anymile-mcp-nanda/1.0"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json"
}


async def make_get_request(url: str) -> dict[str, Any] | None:
    """Make a GET request to the AnyMile API."""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


async def make_post_request(url: str, body: Any) -> dict[str, Any] | None:
    """Make a POST request to the AnyMile API."""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=HEADERS, json=body, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return e


@mcp.tool()
async def get_routes() -> str:
    """Gets the publicly available drone routes from AnyMile"""

    route_url = f"{ANYMILE_URL}/routes"
    route_data = await make_get_request(route_url)

    if not route_data:
        return "Unable to fetch routes this location."

    return route_data


@mcp.tool()
async def get_terminals_by_ids(terminal_ids: list[str]) -> str:
    """Gets the publicly available drone terminals by their IDs

    Args:
        terminal_ids: A list of UUID corresponding to terminal IDs
    """

    joined_ids = ",".join(terminal_ids)
    terminal_url = f"{ANYMILE_URL}/terminal?terminalIds={joined_ids}"
    terminal_data = await make_get_request(terminal_url)

    if not terminal_data:
        return "Unable to fetch terminals."

    return terminal_data


@mcp.tool()
async def create_shipment_package_request(package_type: str, weight: float, height: float, width: float, length: float, description: str):
    """Builds a drone shipment package request

    Args:
        package_type: One of the available package types. This can be fetched from AnyMile
        weight: The weight of the package in kilograms
        height: The height of the package in meters
        width: The width of the package in meters
        length: The length of the package in meters
        description: A description of the contents of the package
    """

    return {
        "amount": 1,
        "packageType": package_type,
        "length": length,
        "width": width,
        "height": height,
        "weight": weight,
        "description": description
    }


@mcp.tool()
async def get_package_types():
    """Retrieves the available package types from AnyMile"""

    url = f"{ANYMILE_URL}/package-types"
    res = await make_get_request(url)

    if not res:
        return "Unable to fetch package types."

    return res


@mcp.tool()
async def get_route_types():
    """Retrieves the available drone route types from AnyMile"""

    url = f"{ANYMILE_URL}/route-types"
    res = await make_get_request(url)

    if not res:
        return "Unable to fetch route types."

    return res


@mcp.tool()
async def get_on_demand_types():
    """Retrieves the available On Demand Types from AnyMile for a Drone Shipment Request."""

    url = f"{ANYMILE_URL}/on-demand-types"
    res = await make_get_request(url)

    if not res:
        return "Unable to fetch on demand types."

    return res


@mcp.tool()
async def get_shipment_types():
    """Retrieves the available Shipment Types from AnyMile for a Shipment Request."""

    url = f"{ANYMILE_URL}/shipment-types"
    res = await make_get_request(url)

    if not res:
        return "Unable to fetch shipment types."

    return res


@mcp.tool()
async def get_recipients():
    """Retrieves a list of recipients for a shipment package"""

    recipients_url = f"{ANYMILE_URL}/recipients"
    recipients = await make_get_request(recipients_url)

    if not recipients:
        return "No recipients available."

    return recipients


@mcp.tool()
async def request_shipment(
    on_demand_type: str,
    shipment_type: str,
    shipper_drop_off_start_time: datetime,
    shipper_drop_off_end_time: datetime,
    shipper_delivery_start_time: datetime,
    shipper_delivery_end_time: datetime,
    origin_terminal_id: str,
    destination_terminal_id: str,
    recipient_id: str,
    shipment_package_request: Any,
):
    """Requests a drone shipment for a package from AnyMile.

    Args:
        on_demand_type: The On Demand type for the shipment request. On Demand Types can be fetched from AnyMile.
        shipment_type: The Shipment type for the shipment request. Shipment Types can be fetched from AnyMile.
        shipper_drop_off_start_time: The starting datetime window in the users timezone for the shipper to drop off the package.
        shipper_drop_off_end_time: The ending datetime window in the users timezone for the shipper to drop off the package.
        shipper_delivery_start_time: The starting datetime window in the users timezone for the delivery to finish.
        shipper_delivery_end_time: The ending datetime window in the users timezone for the delivery to finish.
        origin_terminal_id: The terminal id this package will be shipped from. This value must come from a route.
        destination_terminal_id: The terminal id this package will be shipped to. This value must come from a route.
        recipient_id: The id of the recipient that the user had created or fetched from AnyMile.
        shipment_package_request: A JSON string retrieved from the tool create_shipment_package_request.
    """

    req = {
        "onDemandType": on_demand_type,
        "shipmentType": shipment_type,
        "shipperDropOffStartTime": shipper_drop_off_start_time.isoformat(timespec='milliseconds'),
        "shipperDropOffEndTime": shipper_drop_off_end_time.isoformat(timespec='milliseconds'),
        "shipperRequestedDeliveryStartTime": shipper_delivery_start_time.isoformat(timespec='milliseconds'),
        "shipperRequestedDeliveryEndTime": shipper_delivery_end_time.isoformat(timespec='milliseconds'),
        "originTerminalId": origin_terminal_id,
        "destinationTerminalId": destination_terminal_id,
        "recipientId": recipient_id,
        "packages": [shipment_package_request]
    }

    url = f"{ANYMILE_URL}/shipment"
    res = await make_post_request(url, req)
    return res

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
#    mcp.run(transport='stdio')
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080, timeout_keep_alive=1200)
