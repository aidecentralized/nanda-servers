# AnyMile MCP Server
This project gives you MCP tools that allow you to interact with the AnyMile shipment API.

## AnyMile MCP Tools

### Route Information
- `get_routes` - Retrieves all publicly available shipping routes
- `get_terminals_by_ids` - Gets detailed information about terminals by their IDs
- `get_route_types` - Retrieves the available route types (SHUTTLE, ON_DEMAND)

### Package Configuration
- `get_package_types` - Lists all available package types (e.g., CORRUGATED_BOX, POLY_BAG)
- `create_shipment_package_request` - Creates a package specification with dimensions, weight, and description

### Shipment Options
- `get_on_demand_types` - Lists available on-demand shipping types (COLLECTION, DELIVERY)
- `get_shipment_types` - Lists available shipment types (TERMINAL_TO_TERMINAL, DOOR_TO_DOOR, etc.)

### Recipient Management
- `get_recipients` - Retrieves the list of available recipients

### Shipment Creation
- `request_shipment` - Creates a shipment request with all necessary details including:
  - Origin and destination terminals
  - Package details
  - Recipient information
  - Drop-off and delivery time windows
  - Shipment and on-demand types