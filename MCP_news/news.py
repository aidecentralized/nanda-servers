
import os
from pickle import GET
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
import requests

# Initialize FastMCP server with a name
# This name appears to clients when they connect

import aiohttp
from mcp.server.fastmcp import FastMCP
from urllib.parse import urlencode

mcp = FastMCP("news", dependencies=["aiohttp"])

# loads environment variables from .env file
# (might not be needed on Nanda, need to check)
from dotenv import load_dotenv
load_dotenv()

# gets the NEWS_API_KEY from environment
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# checks for missing key and logs error
if not NEWS_API_KEY:
    mcp.send_log_message(
        level=LogLevel.ERROR,
        data="""API key not found. Set NEWS_API_KEY environment variable
        to an api key provided by thenewsapi.com"""
    )

# base url for thenewsapi.com api calls
BASE_URL = "https://api.thenewsapi.com/v1/news"


async def make_news_request(url: str) -> dict[str, Any] | None:
    """Make a request to the News API with proper error handling.

    This helper function centralizes API communication logic and error handling.
    """
    headers = {
        "Accept": "application/json"  # Request JSON format
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None  # Return None on any error


# Formating output (dict to string)
def format_news_dict_to_string(features: (dict, list, str), output: str = "") -> str:
# A generalized recursive function that converts API response dict to readable strings
# for the output of all endpoint functions
    if features == None:
        features = 'Missing'
    if type(features) is list:
        for value in features:
            output += "\n---\n"
            output = format_news_dict_to_string(value,output)
    elif type(features) is dict:
        keys = list(features.keys())
        for key in keys:
            value = features[key]
            output += f"{key[0].upper()+key[1:]}: "
            output = format_news_dict_to_string(value,output)
    else:
        output += f"{features} \n"

    return output

# Top Stories endpoint on thenewsapi.com

# Define a tool using the @mcp.tool() decorator
# This makes the function available as a callable tool to MCP clients
@mcp.tool()
async def get_top_news(locale: str = "",categories: str = "", search: str= "",
                        search_fields: str = "",exclude_categories: str = "", domains: str= "",
                        exclude_domains: str = "",source_ids: str = "", exclude_source_ids: str= "",
                        language: str = "",published_before: str = "", published_after: str= "",
                        published_on: str = "",sort: str = "", limit: str= "", page: str= "") -> str:
    """Get top news stories.

    Args:
         locale: 2-letter ISO 3166-1 code of the country, default is all countries.
         categories: Comma separated list of categories to include. [general , science , sports , business , health , entertainment , tech , politics , food , travel]
         search: Keywords or a phrase to search for.
         search_fields: Comma separated list of fields to apply the search parameter to. [title, description, keywords, main_text]
         exclude_categories: Comma separated list of categories to exclude.
         domains: Comma separated list of domains to include.
         exclude_domains: Comma separated list of domains to exclude
         source_ids: Comma separated list of source_ids to include.
         exclude_source_ids: Comma separated list of source_ids to exclude.
         language: Comma separated list of languages to include. Default is all.
         published_before: Find all articles published before the specified date.
         published_after: Find all articles published after the specified date.
         published_on: Find all articles published on the specified date.
         sort: Sort by published_on or relevance_score (only available when used in conjunction with search)
         limit: Specify the number of articles you want to return in the request.
         page: Use this to paginate through the result set.

    """

    ### looping url creation: loops through all local variables and adds them to the
    ### url get request if a value was entered

    # add apikey to local
    api_token = NEWS_API_KEY

    #loop through local variables
    features = locals()
    keys = list(features.keys())
    params = {}
    for key in keys:
        value = features[key]
        if type(value) == str:
            # remove whitespace from value
            value = value.strip()
            value = value.lower()
            # check if a value was entered for local variable
            if value != "":
                # add local variable to url
                params[key] = value
        if type(value) == list:
            params[key] = ",".join(value)

    # Construct URL using urlencode
    url = f"{BASE_URL}/top?{urlencode(params)}"

    data = await make_news_request(url)

    if not data:
        return "Unable to fetch news."

    return format_news_dict_to_string(data)

# All News endpoint on thenewsapi.com
@mcp.tool()
async def get_all_news(categories: str ="", language: str = "", search: str= "",
                    search_fields: str = "",exclude_categories: str = "", domains: str= "",
                    exclude_domains: str = "",source_ids: str = "", exclude_source_ids: str= "",
                    published_before: str = "", published_after: str= "",published_on: str = "",
                    sort: str = "", limit: str= "", page: str= "") -> str:
    """
    Use this endpoint to find all live and historical articles we collect.
    Filtering by language, category, source and publish date is also possible,
    as well as advanced searching on title and the main text of the article.

    Args:
         categories: The category of news to fetch [general , science , sports , business , health , entertainment , tech , politics , food , travel]
         language: Comma separated list of languages to include. Default is all.
         search: Keywords or a phrase to search for.
         search_fields: Comma separated list of fields to apply the search parameter to. [title, description, keywords, main_text]
         exclude_categories: Comma separated list of categories to exclude.
         domains: Comma separated list of domains to include.
         exclude_domains: Comma separated list of domains to exclude
         source_ids: Comma separated list of source_ids to include.
         exclude_source_ids: Comma separated list of source_ids to exclude.
         published_before: Find all articles published before the specified date.
         published_after: Find all articles published after the specified date.
         published_on: Find all articles published on the specified date.
         sort: Sort by published_on or relevance_score (only available when used in conjunction with search)
         limit: Specify the number of articles you want to return in the request.
         page: Use this to paginate through the result set.
    """

    ### looping url creation: loops through all local variables and adds them to the
    ### url get request if a value was entered

    # add apikey to local
    api_token = NEWS_API_KEY

    #loop through local variables
    features = locals()
    keys = list(features.keys())
    params = {}
    for key in keys:
        value = features[key]
        if type(value) == str:
            # remove whitespace from value
            value = value.strip()
            value = value.lower()
            # check if a value was entered for local variable
            if value != "":
                # add local variable to url
                params[key] = value
        if type(value) == list:
            params[key] = ",".join(value)

    # Construct URL using urlencode
    url = f"{BASE_URL}/all?{urlencode(params)}"

    data = await make_news_request(url)

    if not data:
        return "Unable to fetch news."

    return format_news_dict_to_string(data)

# Similar News endpoint on thenewsapi.com
@mcp.tool()
async def get_similar_news(uuid: str = "", categories: str = "", language: str = "",
                        exclude_categories: str = "",source_ids: str = "", exclude_source_ids: str= "",
                        published_before: str = "", published_after: str= "",published_on: str = "",
                        limit: str= "", page: str= "") -> str:
    """
    Use this endpoint to find similar stories to a specific article based on its UUID.

    Args:
        uuid: The unique identifier for an article in our system.
        language: Comma separated list of languages to include. Default is all.
        categories: The category of news to fetch [general , science , sports , business , health , entertainment , tech , politics , food , travel]
        exclude_categories: Comma separated list of categories to exclude.
        source_ids: Comma separated list of source_ids to include.
        exclude_source_ids: Comma separated list of source_ids to exclude.
        published_before: Find all articles published before the specified date.
        published_after: Find all articles published after the specified date.
        published_on: Find all articles published on the specified date.
        limit: Specify the number of articles you want to return in the request.
        page: Use this to paginate through the result set.
    """

    ### looping url creation: loops through all local variables and adds them to the
    ### url get request if a value was entered

    # add apikey to local
    api_token = NEWS_API_KEY

    #loop through local variables
    features = locals()
    keys = list(features.keys())
    params = {}
    for key in keys:
        value = features[key]
        if type(value) == str:
            # remove whitespace from value
            value = value.strip()
            value = value.lower()
            # check if a value was entered for local variable
            if value != "":
                # add local variable to url
                params[key] = value
        if type(value) == list:
            params[key] = ",".join(value)

    # Construct URL using urlencode
    url = f"{BASE_URL}/similar/{uuid}?{urlencode(params)}"

    data = await make_news_request(url)

    if not data:
        return "Unable to fetch news."

    return format_news_dict_to_string(data)

# News by UUID endpoint on thenewsapi.com
@mcp.tool()
async def get_article_by_uuid(uuid: str = "") -> str:
    """
    Use this endpoint to find specific articles by the UUID which is returned on our search endpoints.
    This is useful if you wish to store the UUID to return the article later.

    Args:
        uuid: The unique identifier for an article in our system.
    """

    ### looping url creation: loops through all local variables and adds them to the
    ### url get request if a value was entered

    # add apikey to local
    api_token = NEWS_API_KEY

    #loop through local variables
    features = locals()
    keys = list(features.keys())
    params = {}
    for key in keys:
        value = features[key]
        if type(value) == str:
            # remove whitespace from value
            value = value.strip()
            value = value.lower()
            # check if a value was entered for local variable
            if value != "":
                # add local variable to url
                params[key] = value
        if type(value) == list:
            params[key] = ",".join(value)

    # Construct URL using urlencode
    url = f"{BASE_URL}/uuid/{uuid}?{urlencode(params)}"

    data = await make_news_request(url)

    if not data:
        return "Unable to fetch news."

    return format_news_dict_to_string(data)

# Sources endpoint on thenewsapi.com
@mcp.tool()
async def get_news_sources(categories: str = "", language: str = "",exclude_categories: str = "",
                            page: str = "") -> str:
    """
    Use this endpoint to sources to use in your news API requests.
    Note that the limit is 50 for all requests.

    Args:
        categories: The category of news to fetch [general , science , sports , business , health , entertainment , tech , politics , food , travel]
        exclude_categories: Comma separated list of categories to exclude
        language: Comma separated list of languages to include. Default is all.
        page: Use this to paginate through the result set. Default is 1.
    """

    ### looping url creation: loops through all local variables and adds them to the
    ### url get request if a value was entered

    # add apikey to local
    api_token = NEWS_API_KEY

    #loop through local variables
    features = locals()
    keys = list(features.keys())
    params = {}
    for key in keys:
        value = features[key]
        if type(value) == str:
            # remove whitespace from value
            value = value.strip()
            value = value.lower()
            # check if a value was entered for local variable
            if value != "":
                # add local variable to url
                params[key] = value
        if type(value) == list:
            params[key] = ",".join(value)

    # Construct URL using urlencode
    url = f"{BASE_URL}/sources?{urlencode(params)}"

    data = await make_news_request(url)

    if not data:
        return "Unable to fetch news."

    return format_news_dict_to_string(data)


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
