import httpx
import urllib.parse
import logging
from typing import Optional, List, Dict, Any
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

from fastmcp import FastMCP

# Configure logging
logger = logging.getLogger('hyperskill_mcp')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global variable to cache the session ID
_session_id: Optional[str] = None

async def fetch_session_id() -> Optional[str]:
    """Fetches the session ID from Hyperskill API and caches it."""
    global _session_id
    # Avoid fetching again if we already have it
    if _session_id:
        return _session_id

    url = "https://hyperskill.org/api/profiles/current"
    headers = {
        "accept": "application/json",
        # It's generally good practice to identify your client with a proper User-Agent
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient() as client:
            # We don't need the response body, just the cookies, so stream=True might be slightly more efficient
            # but for simplicity, a standard get is fine.
            response = await client.get(url, headers=headers, follow_redirects=True)
            # We don't necessarily need to raise for status, 
            # as a redirect or even a 4xx/5xx might still set cookies, although less likely.
            # response.raise_for_status()

            if "sessionid" in response.cookies:
                _session_id = response.cookies["sessionid"]
                return _session_id
            else:
                logger.warning("Failed to obtain session ID from Hyperskill API response cookies.")
                logger.warning(f"Status Code: {response.status_code}")
                return None

    except httpx.RequestError as exc:
        logger.error(f"Error fetching session ID: An error occurred while requesting {exc.request.url!r}: {exc}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during session ID fetch: {e}")
        return None

mcp = FastMCP("Hyperskill")

async def fetch_parent_topics(topic_ids: List[str]) -> Dict[str, str]:
    """Fetches titles for parent topic IDs.
    
    Args:
        topic_ids: List of parent topic IDs
        
    Returns:
        Dictionary mapping topic IDs to their titles
    """
    if not topic_ids:
        return {}
    
    # Fetch details for all parent topics
    details = await fetch_topic_details(topic_ids)
    
    # Create a mapping of ID to title
    parent_map = {}
    if details and "topics" in details:
        for topic in details["topics"]:
            parent_map[str(topic["id"])] = topic["title"]
    
    return parent_map


@mcp.tool()
async def explain_topics_in_the_code(topics: list[str], programming_language: str) -> list[Dict[str, Any]]:
    """Explain topics in the code
    
    Args:
        topics: List of key topics (or concepts) the user needs to understand to fully grasp given code. Use Hyperskill-compatible topic names like: "for loop", "list comprehensions", "lambda expressions", "decorators", "file I/O", "context managers", etc. Be precise. Avoid duplicates. Avoid overly broad or generic topics.
        programming_language: Programming language of the given code.
    Returns:
        List of dictionaries containing topic id, title, url, hierarchy and clickable link
    """
    topics_details = await find_topics_on_hyperskill(topics, programming_language)
    return topics_details

@mcp.tool()
async def find_topics_on_hyperskill(topics: list[str], programming_language: str) -> list[Dict[str, Any]]:
    """Find topics on Hyperskill and return their details
    
    Args:
        topics: List of topic keywords to search for. Use Hyperskill-compatible topic names like: "for loop", "list comprehensions", "lambda expressions", "decorators", "file I/O", "context managers", etc. Be precise. Avoid duplicates. Avoid overly broad or generic topics.
        programming_language: Programming language to filter topics by.
    Returns:
        List of dictionaries containing topic id, title, url, hierarchy and clickable link
    """
    # First find the topic IDs
    topic_ids = []
    for topic in topics:
        result = await search_hyperskill(topic + " " + programming_language)
        if result:
            topic_ids.append(result)
    
    # If no topics found, return empty list
    if not topic_ids:
        return []
    
    # Fetch details for all found topics
    details = await fetch_topic_details(topic_ids)
    
    # Extract relevant information
    if details and "topics" in details:
        result = []
        
        # Collect all parent topic IDs for batch fetching
        all_parent_ids = []
        for topic in details["topics"]:
            if "hierarchy" in topic and topic["hierarchy"]:
                all_parent_ids.extend([str(id) for id in topic["hierarchy"]])
        
        # Fetch parent topic titles in one batch request
        parent_topic_map = await fetch_parent_topics(list(set(all_parent_ids)))
        
        for topic in details["topics"]:
            # Create hierarchy string if hierarchy exists
            hierarchy_string = ""
            if "hierarchy" in topic and topic["hierarchy"]:
                hierarchy_titles = []
                for parent_id in topic["hierarchy"]:
                    parent_title = parent_topic_map.get(str(parent_id), f"Unknown ({parent_id})")
                    hierarchy_titles.append(parent_title)
                hierarchy_string = " / ".join(hierarchy_titles)
            
            result.append({
                "id": topic["id"],
                "title": topic["title"],
                "url": f"https://hyperskill.org/learn/topic/{topic['id']}",
                "link": f"[{topic['title']}](https://hyperskill.org/learn/topic/{topic['id']})",
                "hierarchy": hierarchy_string
            })
        
        return result
    
    # Return just the IDs if fetching details failed
    return [{"id": tid} for tid in topic_ids]

async def search_hyperskill(keyword: str) -> Optional[str]:
    """Searches Hyperskill for a given keyword and returns the target_id of the first result."""
    # Ensure session ID is fetched/refreshed before proceeding (implicitly via get_session_id)
    # await fetch_session_id() # Removed explicit call

    encoded_keyword = urllib.parse.quote_plus(keyword)
    url = f"https://hyperskill.org/api/search-results?query={encoded_keyword}&include_groups=false&include_projects=false&include_users=false"
    
    headers = {"accept": "application/json"}
    # Now awaits fetch_session_id directly
    session_id = await fetch_session_id()
    if session_id:
        headers["Cookie"] = f"sessionid={session_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            response_data = response.json()
            logger.debug(f"Search response for keyword '{keyword}': {response_data}")

            search_results = response_data.get("search-results") or response_data.get("search_results")

            if search_results and len(search_results) > 0:
                first_result = search_results[0]
                target_id = first_result.get("target_id")
                if target_id:
                    return str(target_id) # Ensure it's returned as a string

            logger.info(f"No search results found for keyword: {keyword}")
            return None
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for '{keyword}': {e}")
        # Consider more specific exception handling if needed
        return None

async def fetch_topic_details(topic_ids: List[str]) -> Optional[Dict[str, Any]]:
    """Fetches detailed information about topics from the Hyperskill API.
    
    Args:
        topic_ids: A list of topic IDs to fetch details for
        
    Returns:
        A dictionary containing the topic details or None if the request fails
    """
    if not topic_ids:
        return None
    
    # Convert list of IDs to comma-separated string
    ids_param = ",".join(topic_ids)
    url = f"https://hyperskill.org/api/topics?ids={ids_param}"
    
    headers = {"accept": "application/json"}
    session_id = await fetch_session_id()
    if session_id:
        headers["Cookie"] = f"sessionid={session_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching topic details: {e}")
        return None

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
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    logger.info("Starting Hyperskill MCP Server")
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)