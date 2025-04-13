# mcp-web-crawler

This project provides a Model Context Protocol (MCP) server built with Python using `FastMCP`. It allows MCP clients (like AI assistants or other applications) to scrape a website using the `crawl4ai` library.

At j16z we are using it as part of Covercraft - to fetch information about job listings, companies, etc.

This MCP server is a part of [j16z](https://j16z.org)'s offering of MCP servers as an active collaborator of MIT's [Nanda registry](https://nanda.media.mit.edu/). The Nanda explorer can be found here: https://ui.nanda-registry.com/explorer

## Prerequisites

*   Python (v3.8 or later recommended)
*   [uv](https://docs.astral.sh/uv/getting-started/installation/) (An extremely fast Python package installer and resolver)

## Installation & Setup

1.  **Install uv (if you haven't already):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    ```

2.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd mcp-linkedin-jobs
    ```
    *(Replace `<your-repository-url>` with the actual URL)*

3.  **Install dependencies using uv:**
    ```bash
    uv add fastmcp crawl4ai tenacity # this will create a .venv as well and select ut
    # Add any other direct dependencies here (e.g., uvicorn if needed)
    ```
    *This command adds the packages to your `pyproject.toml` and installs them.*

5.  **Run the setup for crawl4ai:**
    ```bash
    crawl4ai-setup
    # Verify your installation (optional but recommended)
    crawl4ai-doctor
    ```
    *(If you encounter issues, refer to the [crawl4ai GitHub repository](https://github.com/unclecode/crawl4ai))*

## Running Locally

1.  **Ensure the virtual environment is activated:**
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the server script directly:**
    *   Assuming your main server script is `server.py`:
        ```bash
        python server.py
        ```
    *(This is generally preferred over `mcp dev` for running just the server without the      inspector interference.)*
    A Runner like PM2 can be used as well, and is recommended. That would look like:
    ```bash
    pm2 start server.py --name "mcp-web-crawler" --interpreter /root/mcp-webcrawler/.venv/bin/python
    ```

    The server will start and listen for connections, typically on `http://localhost:3001` (or as configured). It uses Server-Sent Events (SSE) for communication.

## Testing Locally (Using `curl`)

You can test the running server using `curl` from your command line.

Run: `curl -I http://localhost:3001/sse` to ensure the server is running locally.



## Available Tools

The server currently exposes the following tools for MCP clients:

1.  **`crawl_job_posting`**
    *   **Description:** Crawls a specific job posting page to extract the job description.
    *   **Arguments:**
        *   `url` (string, **required**): The direct URL of the job posting.
    *   **Example JSON Arguments:** `{ "url": "https://jobs.lever.co/openai/12345abcde" }`

## Example Client Queries

An AI assistant integrated with this server could potentially handle requests like:

*   "Get the job description from this URL: https://..." (Uses `crawl_job_posting`)
*   "Find company context for example.com, don't go deeper than 1 level." (Uses `crawl_company_context`)
*   "Get the job details and company background for this posting: https://..." (Uses `smart_crawl_job`)
*   "Process these job listings: [list of URLs]" (Uses `batch_smart_crawl_jobs`)

## Deployment Guide

Will be added soon.

## Project Structure (Example)

*   `server.py` (or `main.py`): Main script to configure and start the FastMCP server.
*   `tools/mcp_tools.py`: Defines the `MCPToolManager` class and registers the crawling tools.
*   `pyproject.toml`: Project metadata and dependencies (managed by `uv`).
*   `.venv/`: Python virtual environment created by `uv`.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `README.md`: This file.

## Technologies Used

*   Python 3
*   `uv` (Package installer/resolver)
*   `fastmcp` (Python MCP SDK)
*   `crawl4ai` (Core web crawling and content processing library)
*   `asyncio` (For asynchronous operations)
*   `tenacity` (For retry logic)

## Notes

*   Web crawling can be resource-intensive. Ensure the server has adequate memory and CPU.
*   Be mindful of website `robots.txt` files and terms of service. `crawl4ai` has options for respecting `robots.txt`.
*   Rate limiting on target websites is common. The `tenacity` retry logic helps, but consider adding delays or more sophisticated rate-limiting handling if needed.