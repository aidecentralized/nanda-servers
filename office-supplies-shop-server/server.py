from typing import Any, List, Dict, Optional
import csv
import os
import httpx
from mcp.server.fastmcp import FastMCP  # Main MCP server class
from starlette.applications import Starlette  # ASGI framework
from starlette.responses import HTMLResponse  # Add HTML response
from mcp.server.sse import SseServerTransport  # SSE transport implementation
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server  # Base server class
import uvicorn  # ASGI server

# Initialize FastMCP server with a name
# This name appears to clients when they connect
mcp = FastMCP("inventory")

# Path to the inventory CSV file - adjust this if needed
INVENTORY_CSV_PATH = "inventory.csv"

# Debug mode for additional logging
DEBUG = True

def debug_log(message: str) -> None:
    """Print debug messages if DEBUG is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}")

# Cache for inventory data to avoid reading the file on every request
_inventory_cache: Optional[List[Dict[str, Any]]] = None


def load_inventory() -> List[Dict[str, Any]]:
    """Load inventory data from CSV file.
    
    Returns:
        List of dictionaries, where each dictionary represents an inventory item.
    """
    global _inventory_cache
    
    # Return cached data if available
    if _inventory_cache is not None:
        return _inventory_cache
    
    # Ensure the file exists
    if not os.path.exists(INVENTORY_CSV_PATH):
        raise FileNotFoundError(f"Inventory file not found: {INVENTORY_CSV_PATH}")
    
    inventory_items = []
    
    # Read CSV file
    with open(INVENTORY_CSV_PATH, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Validate that required columns exist
        fieldnames = reader.fieldnames
        if not fieldnames or 'item_name' not in fieldnames:
            raise ValueError(f"CSV file missing required 'item_name' column. Available columns: {fieldnames}")
        
        for row in reader:
            # Convert numeric fields to appropriate types
            for field in ['quantity', 'minimum_stock']:
                if field in row and row[field]:
                    try:
                        row[field] = int(row[field])
                    except ValueError:
                        # If conversion fails, keep as string
                        pass
            
            for field in ['unit_price']:
                if field in row and row[field]:
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        # If conversion fails, keep as string
                        pass
                    
            inventory_items.append(row)
    
    # Cache the data
    _inventory_cache = inventory_items
    return inventory_items


def refresh_inventory_cache() -> None:
    """Force a refresh of the inventory cache.
    
    Call this when you know the inventory file has changed.
    """
    global _inventory_cache
    _inventory_cache = None


# Define a tool using the @mcp.tool() decorator
@mcp.tool()
async def get_items() -> str:
    """Get a list of all item names in the inventory.
    
    Returns:
        A formatted string listing all item names in the inventory.
    """
    try:
        debug_log("Loading inventory data")
        inventory = load_inventory()
        
        if not inventory:
            return "The inventory is empty."
        
        debug_log(f"Loaded {len(inventory)} items")
        
        # Extract all item names with error handling for each item
        item_names = []
        for i, item in enumerate(inventory):
            try:
                if 'item_name' not in item:
                    debug_log(f"Item {i} missing 'item_name' field. Available keys: {list(item.keys())}")
                    continue
                    
                item_names.append(item['item_name'])
            except Exception as e:
                debug_log(f"Error processing item {i}: {str(e)}")
        
        debug_log(f"Found {len(item_names)} valid item names")
        
        # Format the result
        result = "Available items in inventory:\n\n"
        for i, name in enumerate(item_names, 1):
            result += f"{i}. {name}\n"
        
        return result
    
    except FileNotFoundError as e:
        error_msg = f"Error: {str(e)}"
        debug_log(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"An error occurred while retrieving inventory items: {str(e)}"
        debug_log(error_msg)
        return error_msg


@mcp.tool()
async def get_item_info(item_name: str) -> str:
    """Get detailed information about a specific item in the inventory.
    
    Args:
        item_name: The name of the item to look up
        
    Returns:
        A formatted string containing all information about the specified item,
        or an error message if the item is not found.
    """
    try:
        inventory = load_inventory()
        
        # Find the item in the inventory
        item = None
        for inv_item in inventory:
            if inv_item['item_name'].lower() == item_name.lower():
                item = inv_item
                break
        
        # If exact match not found, try partial matching
        if item is None:
            for inv_item in inventory:
                if item_name.lower() in inv_item['item_name'].lower():
                    item = inv_item
                    break
        
        if item is None:
            return f"Item '{item_name}' not found in the inventory."
        
        # Format the item information
        result = f"Information for: {item['item_name']}\n\n"
        
        for key, value in item.items():
            # Skip item_name since it's already in the header
            if key != 'item_name':
                # Format the key for better readability
                formatted_key = ' '.join(word.capitalize() for word in key.split('_'))
                result += f"{formatted_key}: {value}\n"
        
        return result
    
    except FileNotFoundError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"An error occurred while retrieving item information: {str(e)}"


# Add a homepage handler for root URL
async def homepage(request: Request) -> HTMLResponse:
    """Handle requests to the root URL by returning a simple HTML page."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Inventory Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            .status {
                padding: 10px;
                background-color: #e6f7e6;
                border-left: 4px solid #28a745;
                margin-bottom: 20px;
            }
            button {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0069d9;
            }
            #status-box {
                margin-top: 20px;
                padding: 10px;
                border: 1px solid #ddd;
                min-height: 100px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MCP Inventory Server</h1>
            <div class="status">Server is running correctly!</div>
            
            <button id="connect-btn">Connect to SSE</button>
            
            <div id="status-box">Connection status will appear here...</div>
            
            <h2>Available Tools:</h2>
            <ul>
                <li><strong>get_items</strong> - Get a list of all items in the inventory</li>
                <li><strong>get_item_info</strong> - Get detailed information about a specific item</li>
            </ul>
            
            <script>
                document.getElementById('connect-btn').addEventListener('click', function() {
                    const statusBox = document.getElementById('status-box');
                    statusBox.innerHTML = 'Connecting to SSE...';
                    
                    try {
                        const eventSource = new EventSource('/sse');
                        
                        eventSource.onopen = function() {
                            statusBox.innerHTML += '<br>Connection established!';
                        };
                        
                        eventSource.onerror = function(error) {
                            statusBox.innerHTML += '<br>Error: Connection failed';
                            eventSource.close();
                        };
                        
                        eventSource.addEventListener('message', function(event) {
                            statusBox.innerHTML += `<br>Received: ${event.data}`;
                        });
                    } catch (error) {
                        statusBox.innerHTML += `<br>Error: ${error.message}`;
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Create a Starlette application with SSE transport
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE.
    
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
            Route("/", endpoint=homepage),  # Add root URL handler
            Route("/sse", endpoint=handle_sse),  # Endpoint for SSE connections
            Mount("/messages/", app=sse.handle_post_message),  # Endpoint for messages
        ],
    )


if __name__ == "__main__":
    # Get the underlying MCP server from FastMCP wrapper
    mcp_server = mcp._mcp_server

    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Inventory MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    print(f"Starting Inventory MCP Server on {args.host}:{args.port}")
    print(f"Inventory file: {INVENTORY_CSV_PATH}")
    
    try:
        # Test loading the inventory to catch errors early
        inventory_count = len(load_inventory())
        print(f"Successfully loaded {inventory_count} inventory items")
    except Exception as e:
        print(f"Error loading inventory: {e}")
        print("Server will still start, but tools may not work correctly")

    # Create and run the Starlette application
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
