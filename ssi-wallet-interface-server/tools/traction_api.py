import os
import asyncio
import json
import aiohttp
from mcp.server.fastmcp import FastMCP
import logging
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TENANT_ID = os.getenv("TENANT_ID", "").strip()
API_KEY = os.getenv("API_KEY", "").strip()
TRACTION_BASE_URL = os.getenv("TRACTION_BASE_URL", "").strip()


print("API_TOOL")
print("TENANT_ID:", repr(TENANT_ID))
print("API_KEY:", repr(API_KEY))

# TRACTION_BASE_URL = "http://traction_api.xanaducyber.com"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

mcp = FastMCP("AcaPyMCPToolsEnriched")
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=10)

async def http_request(method: str, path: str, payload: dict = None, headers: dict = None) -> dict:
    url = TRACTION_BASE_URL.rstrip("/") + path
    logger.info("Making %s request to %s", method.upper(), url)
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async def parse_response(resp):
            if resp.status not in (200, 201):
                error_text = await resp.text()
                logger.error("Error response (%s): %s", resp.status, error_text)
                return {"error": error_text, "status": resp.status}
            return await resp.json()

        if method.lower() == "get":
            async with session.get(url, params=payload, headers=headers) as resp:
                return await parse_response(resp)
        elif method.lower() == "post":
            async with session.post(url, json=payload, headers=headers) as resp:
                return await parse_response(resp)
        elif method.lower() == "put":
            async with session.put(url, json=payload, headers=headers) as resp:
                return await parse_response(resp)
        elif method.lower() == "delete":
            async with session.delete(url, json=payload, headers=headers) as resp:
                return await parse_response(resp)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

async def get_bearer_token() -> str:
    logger.info("Tool get_bearer_token called with TENANT_ID: %s and API_KEY: %s", TENANT_ID, API_KEY)
    if not TENANT_ID or not API_KEY:
        logger.error("TENANT_ID or API_KEY not set")
        return "Error: TENANT_ID or API_KEY is missing"

    path = f"/multitenancy/tenant/{TENANT_ID}/token"
    payload = {
        "api_key": API_KEY
    }
    headers = {
        "Content-Type": "application/json"
    }

    result = await http_request("post", path, payload=payload, headers=headers)
    token = result.get("token", "")
    if not token:
        logger.error("Failed to retrieve token: %s", result)
        return "Error: Unable to retrieve token"
    logger.info("Successfully retrieved token.")
    return token

@mcp.tool()
async def get_tenant_details() -> str:
    """
    Retrieves tenant details using the provided bearer token.
    
    Returns:
        A JSON-formatted string representing tenant details.
    """

    token = await get_bearer_token()

    logger.info("Tool get_tenant_details called with token: %s", token)
    headers = {"Authorization": f"Bearer {token}"}
    result = await http_request("get", "/tenant", headers=headers)
    logger.info("get_tenant_details successfully retrieved tenant details.")
    return json.dumps(result, indent=2)

@mcp.tool()
async def query_connections(
    alias: str = None,
    connection_protocol: str = None,
    invitation_key: str = None,
    invitation_msg_id: str = None,
    limit: int = 100,
    my_did: str = None,
    offset: int = 0,
    state: str = "active",
    their_did: str = None,
    their_public_did: str = None,
    their_role: str = None
) -> str:
    """
    Query agent-to-agent connections using the /connections endpoint.

    Args:
        alias: Optional alias filter.
        connection_protocol: Optional connection protocol filter.
        invitation_key: Optional invitation key filter.
        invitation_msg_id: Optional invitation message ID filter.
        limit: Number of results to return (default: 100).
        my_did: Filter by my DID.
        offset: Pagination offset (default: 0).
        their_did: Optional Filter by their DID.
        their_public_did: Optional Filter by their public DID.
        their_role: Optional Filter by their role.
        state: Optional Filter by connection status

    Returns:
        JSON-formatted string containing the list of connections or an error message.
    """
    logger.info("Tool list_connections called")

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}

    params = {
        "alias": alias,
        "connection_protocol": connection_protocol,
        "invitation_key": invitation_key,
        "invitation_msg_id": invitation_msg_id,
        "limit": limit,
        "my_did": my_did,
        "offset": offset,
        "state": state,
        "their_did": their_did,
        "their_public_did": their_public_did,
        "their_role": their_role
    }

    # Remove keys with None values to avoid unnecessary query params
    query_params = {k: v for k, v in params.items() if v is not None}

    result = await http_request("get", "/connections", payload=query_params, headers=headers)
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_out_of_band_invitation(
    alias: str = "Default Alias",
    handshake: bool = True,
    metadata: dict = None,
    use_public_did: bool = False,
    my_label: str = "Default Label"
) -> str:
    """
    Create a new out-of-band invitation by calling the /out-of-band/create-invitation endpoint.
    
    This implementation follows the Aries RFC 0434 guidelines for out‑of‑band protocols.
    
    Args:
        alias: An optional alias for the invitation.
        handshake: Determines whether to include handshake protocols.
        metadata: Additional metadata to include in the invitation.
        use_public_did: If true, the public DID is used.
        my_label: A label used in the invitation.
    
    Returns:
        A JSON-formatted string representing the invitation or an error message.
    """
    logger.info(
        "Tool create_out_of_band_invitation called with API_KEY: %s, alias: %s, handshake: %s, metadata: %s, use_public_did: %s, my_label: %s",
         API_KEY, alias, handshake, metadata, use_public_did, my_label
    )
    
    # Build the invitation payload based on RFC 0434:
    payload = {
        "alias": alias,
        "my_label": my_label,
        "use_public_did": use_public_did,
    }
    # Include handshake protocols if handshake flag is true.
    if handshake:
        payload["handshake_protocols"] = ["https://didcomm.org/didexchange/1.0"]
    # Optionally include metadata if provided.
    if metadata:
        payload["metadata"] = metadata

    # Set headers including the authorization and proper content type.

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}

    path = "/out-of-band/create-invitation"
    result = await http_request("post", path, payload=payload, headers=headers)
    
    # Specify the base URL (ngrok URL)
    base_url = "https://92ce-80-40-22-48.ngrok-free.app"
    
    # Verify if the result contains the invitation.
    if "invitation" not in result:
        return json.dumps(result, indent=2)
    
    invitation = result["invitation"]
    
    # Serialize invitation dictionary to a compact JSON string.
    invitation_json = json.dumps(invitation, separators=(',', ':'))
    logger.debug("Serialized invitation JSON: %s", invitation_json)
    
    # Encode the JSON as URL-safe Base64 and remove any trailing '=' padding.
    encoded_invitation = base64.urlsafe_b64encode(invitation_json.encode("utf-8")).decode("utf-8").rstrip("=")
    
    # Construct the final connection URL using the base URL and the encoded invitation.
    connection_url = f"{base_url}?oob={encoded_invitation}"
    
    return connection_url



@mcp.tool()
async def create_schema(
    attributes: list,
    schema_name: str,
    schema_version: str,
    conn_id: str = None,
    create_transaction_for_endorser: bool = False
) -> str:
    """
    Create and send a schema to the ledger via the /schemas endpoint.

    Args:
        attributes: List of schema attribute names.
        schema_name: Name of the schema.
        schema_version: Version of the schema.
        conn_id: Optional connection ID for endorser flow.
        create_transaction_for_endorser: If true, prepares a transaction for an endorser.

    Returns:
        JSON-formatted string containing the response or error message.
    """
    logger.info("Tool create_schema called with schema_name=%s version=%s", schema_name, schema_version)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    payload = {
        "attributes": attributes,
        "schema_name": schema_name,
        "schema_version": schema_version
    }

    # Compose query params
    query = []
    if conn_id:
        query.append(f"conn_id={conn_id}")
    if create_transaction_for_endorser:
        query.append("create_transaction_for_endorser=true")

    query_string = "?" + "&".join(query) if query else ""

    result = await http_request("post", f"/schemas{query_string}", payload=payload, headers=headers)
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_created_schemas(
    schema_id: str = None,
    schema_issuer_did: str = None,
    schema_name: str = None,
    schema_version: str = None
) -> str:
    """
    Retrieve schemas created by this agent using the /schemas/created endpoint.

    Args:
        schema_id: Optional filter by full schema ID.
        schema_issuer_did: Optional filter by issuer DID.
        schema_name: Optional filter by schema name.
        schema_version: Optional filter by schema version.

    Returns:
        A JSON-formatted string containing schema IDs or an error message.
    """
    logger.info("Tool get_created_schemas called")

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    params = {
        "schema_id": schema_id,
        "schema_issuer_did": schema_issuer_did,
        "schema_name": schema_name,
        "schema_version": schema_version,
    }

    # Remove any None values from query parameters
    query_params = {k: v for k, v in params.items() if v is not None}

    result = await http_request("get", "/schemas/created", payload=query_params, headers=headers)
    return json.dumps(result, indent=2)

# @mcp.tool()
# async def list_schemas_in_storage() -> str:
#     """
#     Retrieve all schemas stored in schema storage.

#     Returns:
#         JSON-formatted string of the schema list, including metadata such as schema_id,
#         state, and timestamps.
#     """
#     logger.info("Tool list_schemas called")

#     headers = {"Authorization": f"Bearer {await get_bearer_token()}"}

#     result = await http_request(
#         "get",
#         "/schema-storage",
#         headers=headers
#     )

#     return json.dumps(result, indent=2)

# @mcp.tool()
# async def delete_schema(schema_id: str) -> str:
#     """
#     Delete a schema from schema storage using its identifier.

#     Args:
#         schema_id: The unique identifier of the schema to delete.

#     Returns:
#         JSON-formatted string indicating success or failure of deletion.
#     """
#     logger.info("Tool delete_schema called with schema_id=%s", schema_id)

#     headers = {"Authorization": f"Bearer {await get_bearer_token()}"}

#     result = await http_request(
#         "delete",
#         f"/schema-storage/{schema_id}",
#         headers=headers
#     )

#     return json.dumps(result, indent=2)

@mcp.tool()
async def get_schema_by_id(schema_id: str) -> str:
    """
    Retrieve a schema definition from the ledger by schema_id.

    Args:
        API_KEY: Bearer token for API access.
        schema_id: Fully-qualified schema ID (e.g., DID:2:name:version).

    Returns:
        A JSON-formatted string representing the schema or an error message.
    """
    logger.info("Tool get_schema_by_id called with schema_id=%s", schema_id)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    encoded_schema_id = schema_id.replace(":", "%3A")  # Optional: manual encoding

    path = f"/schemas/{encoded_schema_id}"
    result = await http_request("get", path, headers=headers)

    return json.dumps(result, indent=2)

@mcp.tool()
async def create_credential_definition(
    schema_id: str,
    support_revocation: bool,
    tag: str = "default",
    revocation_registry_size: int = None,
    conn_id: str = None,
    create_transaction_for_endorser: bool = False
) -> str:
    """
    Create and send a credential definition to the ledger.

    Args:
        schema_id: ID of the schema to base the credential definition on.
        support_revocation: Whether the credential supports revocation.
        tag: Optional tag name for the definition (default "default").
        revocation_registry_size: Optional revocation registry size.
        conn_id: Optional endorser connection ID.
        create_transaction_for_endorser: Whether to prepare for endorsement.

    Returns:
        A JSON-formatted string containing the response or an error.
    """
    logger.info("Tool create_credential_definition called with schema_id=%s", schema_id)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    payload = {
        "schema_id": schema_id,
        "support_revocation": support_revocation,
        "tag": tag
    }

    if revocation_registry_size is not None:
        payload["revocation_registry_size"] = revocation_registry_size

    query = []
    if conn_id:
        query.append(f"conn_id={conn_id}")
    if create_transaction_for_endorser:
        query.append("create_transaction_for_endorser=true")

    query_string = "?" + "&".join(query) if query else ""

    result = await http_request("post", f"/credential-definitions{query_string}", payload=payload, headers=headers)
    return json.dumps(result, indent=2)


@mcp.tool()
async def send_message(conn_id: str, content: str) -> str:
    """
    Send a message to a connection.

    Args:
        conn_id: The connection ID to which the message will be sent.
        content: The text content of the message.

    Returns:
        A JSON-formatted string with the response.
    """
    logger.info("Tool send_basic_message called with conn_id=%s, content=%s", conn_id, content)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    payload = {"content": content}

    result = await http_request(
        "post",
        f"/connections/{conn_id}/send-message",
        payload=payload,
        headers=headers
    )
    return json.dumps(result, indent=2)

@mcp.tool()
async def query_basic_messages(
    connection_id: str = None,
    state: str = None  # 'sent' or 'received'
) -> str:
    """
    Query basic messages from all agents (basicmessage_storage v1_0 plugin).

    Args:
        connection_id: Optional filter to limit messages to a specific connection ID.
        state: Optional filter for message state: 'sent' or 'received'.

    Returns:
        A JSON-formatted string with the list of basic messages.
    """
    logger.info("Tool query_basic_messages called with connection_id=%s, state=%s", connection_id, state)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    params = {}

    if connection_id:
        params["connection_id"] = connection_id
    if state:
        params["state"] = state

    result = await http_request("get", "/basicmessages", payload=params, headers=headers)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_created_credential_definitions(
    cred_def_id: str = None,
    issuer_id: str = None,
    schema_id: str = None,
    schema_issuer_did: str = None,
    schema_name: str = None,
    schema_version: str = None
) -> str:
    """
    Retrieve credential definitions created by this agent.

    Args:
        cred_def_id: Optional filter by credential definition ID.
        issuer_id: Optional filter by issuer DID.
        schema_id: Optional filter by schema ID.
        schema_issuer_did: Optional filter by schema issuer DID.
        schema_name: Optional filter by schema name.
        schema_version: Optional filter by schema version.

    Returns:
        A JSON-formatted string with the list of credential definition IDs.
    """
    logger.info("Tool get_created_credential_definitions called")

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}
    params = {
        "cred_def_id": cred_def_id,
        "issuer_id": issuer_id,
        "schema_id": schema_id,
        "schema_issuer_did": schema_issuer_did,
        "schema_name": schema_name,
        "schema_version": schema_version
    }

    # Clean up None values to avoid invalid query params
    query_params = {k: v for k, v in params.items() if v is not None}

    result = await http_request("get", "/credential-definitions/created", payload=query_params, headers=headers)
    return json.dumps(result, indent=2)

@mcp.tool()
async def issue_credential_v2(
    connection_id: str,
    cred_def_id: str,
    schema_id: str,
    attributes: dict,
    auto_remove: bool = True,
    comment: str = "Issuing credential"
) -> str:
    """
    Issue a verifiable credential using the issue-credential-2.0/send endpoint.

    Args:
        connection_id: The connection ID to send the credential to.
        cred_def_id: Credential definition ID.
        schema_id: Schema ID the credential is based on.
        attributes: Dictionary of attribute names and values.
        auto_remove: Whether to remove the exchange record after issuance (default True).
        comment: Optional comment for context.

    Returns:
        JSON-formatted string with the response or error.
    """
    logger.info("Tool issue_credential_v2 called with connection_id=%s", connection_id)

    headers = {"Authorization": f"Bearer {await get_bearer_token()}"}

    credential_preview = {
        "@type": "issue-credential/2.0/credential-preview",
        "attributes": [
            {
                "name": k,
                "value": v,
                "mime-type": "text/plain"  # Adjust as needed
            } for k, v in attributes.items()
        ]
    }

    payload = {
        "auto_remove": auto_remove,
        "comment": comment,
        "connection_id": connection_id,
        "credential_preview": credential_preview,
        "filter": {
            "indy": {
                "cred_def_id": cred_def_id,
                "schema_id": schema_id
            }
        }
    }

    result = await http_request("post", "/issue-credential-2.0/send", payload=payload, headers=headers)
    return json.dumps(result, indent=2)



if __name__ == '__main__':
    # Run the MCP server over stdio.
    mcp.run(transport="stdio")