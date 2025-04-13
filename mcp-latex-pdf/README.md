# mcp-latex-pdf: A Document Conversion MCP Server from LaTeX to PDF

This project provides a Model Context Protocol (MCP) server built with Python using `FastMCP` based on [the SSE transport](https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse) mechanism. It allows MCP clients (like AI assistants or other applications) to convert a LaTeX document to PDFs (with support for more document formats upcoming in the future).

At j16z we are using it as part of Covercraft - to create professional and beautifully typeset cover letters. Example of one such cover letter-

<p align="center">
<img width="521" alt="image" src="https://github.com/user-attachments/assets/a677ebf0-cae1-4d3c-91c8-d01ce614dcd7" />
</p>

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
    git clone <repository-url>
    cd mcp-latex-pdf
    ```
    *(Replace `<your-repository-url>` with the actual URL)*

3.  **Install dependencies using uv:**
    ```bash
    uv add fastmcp docker # this will create a .venv as well and select ut
    # Add any other direct dependencies here (e.g., uvicorn if needed)
    ```
    *This command adds the packages to your `pyproject.toml` and installs them.*

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
    pm2 start server.py --name "mcp-latex-pdf" --interpreter /root/mcp-latex-pdf/.venv/bin/python
    ```

    The server will start and listen for connections, typically on `http://localhost:3001` (or as configured). It uses Server-Sent Events (SSE) for communication.

## Testing Locally (Using `curl`)

You can test the running server using `mcpinspector`.


## Available Tools

The server currently exposes the following tools for MCP clients:

1.  **`crawl_job_posting`**
    *   **Description:** Crawls a specific job posting page to extract the job description.
    *   **Arguments:**
        *   `url` (string, **required**): The direct URL of the job posting.
    *   **Example JSON Arguments:** `{ "url": "https://jobs.lever.co/openai/12345abcde" }`

## Example Client Queries

An AI assistant integrated with this server could potentially handle requests like:

*   "Convert this latex file into a PDF" (Uses `convert-contents`)

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
*   `docker` (accessing the locally running Docker instance)
*   `asyncio` (For asynchronous operations)

## Notes

* Ensure that your docker container is running in a server before using this MCP server. Our current server instance is running at latexpdf.j16z.org.
* The server is capable of generating beautiful looking LaTeX output-
<p align="center">
<img width="478" alt="image" src="https://github.com/user-attachments/assets/b588db9f-e9b8-441e-8b29-5affb2c3826f" />
</p>
