import argparse
import json
import logging
import os
import re
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import arxiv
import uvicorn
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configuration - Simple papers directory
PAPERS_DIR = os.environ.get(
    "PAPERS_DIR", os.path.expanduser("~/Downloads/arxiv_papers")
)

# Create necessary directory
if not os.path.exists(PAPERS_DIR):
    os.makedirs(PAPERS_DIR)
    logger.info(f"Created papers directory: {PAPERS_DIR}")


# Set up the application context
@dataclass
class AppContext:
    pass  # We don't need any context for now


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize application components"""
    logger.info("Starting arXiv Helper")
    yield AppContext()
    logger.info("Shutting down arXiv Helper")


# Create the MCP server with necessary dependencies
mcp = FastMCP(
    "arXiv Helper",
    lifespan=app_lifespan,
    dependencies=["arxiv==1.4.2"],
)


# Helper functions
def sanitize_filename(title):
    """Create a safe filename from a paper title"""
    # Remove characters that are not allowed in filenames
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    # Replace spaces with underscores
    safe_title = safe_title.replace(" ", "_")
    # Truncate if too long (max 255 chars is safe for most filesystems)
    if len(safe_title) > 250:
        safe_title = safe_title[:250]
    return safe_title


def extract_arxiv_id(filename):
    """Extract arXiv ID from filename"""
    # Try to extract numeric ID like 1234.56789
    match = re.search(r"(\d{4}\.\d{4,5}v?\d*)", filename)
    if match:
        return match.group(1)

    # Try to extract old-style ID like cs/9901001
    match = re.search(r"([a-z-]+/\d{7}v?\d*)", filename)
    if match:
        return match.group(1)

    return None


# Comprehensive arXiv pattern detection
def is_arxiv_paper(filename):
    """Check if a filename matches common arXiv paper patterns"""
    arxiv_patterns = [
        r"arXiv_\d+\.\d+v?\d*",  # Pattern like arXiv_1234.56789 or arXiv_1234.56789v1
        r"\d{4}\.\d{4,5}v?\d*",  # Pattern like 2301.12345 or 2301.12345v1
        r"arxiv.*\d{4}\.\d{4,5}",  # Pattern with arxiv and identifier
        r"\d{4}\.\d{4,5}\.pdf",  # Pattern like 2301.12345.pdf
        r"[a-z-]+/\d{7}v?\d*",  # Old-style arXiv ID like cs/9901001
        r"paper_\d{4}\.\d{4,5}v?\d*",  # Pattern like paper_1234.56789
        r".*\d{4}\.\d{4,5}.*\.pdf",  # Any PDF with arXiv-like number pattern
    ]

    for pattern in arxiv_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False


# Resources
@mcp.resource("arxiv://schema")
def get_schema() -> str:
    """Get the schema of the arXiv Helper functionality"""
    return """
    The arXiv Helper provides easy tools to manage arXiv papers:

    1. DETECTING PAPERS:
       - arxiv_detect_directory: Check a directory for arXiv papers
       - arxiv_is_paper: Check if a specific file is an arXiv paper

    2. ORGANIZING PAPERS:
       - arxiv_rename_papers: Rename arXiv papers based on their titles
       - arxiv_list_papers: List all downloaded papers

    3. FINDING & DOWNLOADING PAPERS:
       - arxiv_search_papers: Search for papers on arXiv.org
       - arxiv_download_paper: Download a paper by its arXiv ID
    """


@mcp.resource("arxiv://papers")
def arxiv_list_papers() -> str:
    """List all downloaded papers in the papers folder"""
    papers = []

    for filename in os.listdir(PAPERS_DIR):
        if filename.endswith(".pdf"):
            papers.append(
                {"filename": filename, "path": os.path.join(PAPERS_DIR, filename)}
            )

    return json.dumps({"papers": papers}, indent=2)


@mcp.resource("arxiv://paper/{paper_id}")
def arxiv_paper_info(paper_id: str) -> str:
    """Get metadata for a specific paper"""
    try:
        # Clean the ID (sometimes it comes with the arxiv.org prefix)
        if "/" in paper_id and "arxiv.org" in paper_id:
            paper_id = paper_id.split("/")[-1]

        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results())

        return json.dumps(
            {
                "id": paper.entry_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.strftime("%Y-%m-%d"),
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tools
@mcp.tool()
def arxiv_is_paper(file_path: str) -> str:
    """
    Check if a specific file is an arXiv paper

    Args:
        file_path: Path to the file to check

    Returns:
        JSON string with detection result
    """
    # Check if the file exists and is a PDF
    if not os.path.exists(file_path):
        return json.dumps({"is_arxiv_paper": False, "reason": "File not found"})

    if not file_path.lower().endswith(".pdf"):
        return json.dumps({"is_arxiv_paper": False, "reason": "Not a PDF file"})

    # Check for arXiv identifiers in the filename
    filename = os.path.basename(file_path)

    if is_arxiv_paper(filename):
        return json.dumps(
            {"is_arxiv_paper": True, "arxiv_id": extract_arxiv_id(filename)}
        )

    return json.dumps(
        {"is_arxiv_paper": False, "reason": "No arXiv identifier detected in filename"}
    )


@mcp.tool()
def arxiv_detect_directory(directory_path: str) -> str:
    """
    Detect arXiv papers in a directory

    Args:
        directory_path: Directory to check for arXiv papers

    Returns:
        JSON string with detection results
    """
    # Expand ~ to home directory if present
    if directory_path.startswith("~"):
        directory_path = os.path.expanduser(directory_path)

    if not os.path.isdir(directory_path):
        return json.dumps(
            {"contains_arxiv_papers": False, "reason": "Not a valid directory"}
        )

    # Look for PDF files in the directory
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]

    # Check if any of them are arXiv papers
    arxiv_papers = []
    non_arxiv_papers = []

    for pdf in pdf_files:
        file_path = os.path.join(directory_path, pdf)
        if is_arxiv_paper(pdf):
            arxiv_id = extract_arxiv_id(pdf)
            arxiv_papers.append(
                {"filename": pdf, "path": file_path, "arxiv_id": arxiv_id}
            )
        else:
            non_arxiv_papers.append({"filename": pdf, "path": file_path})

    return json.dumps(
        {
            "contains_arxiv_papers": len(arxiv_papers) > 0,
            "arxiv_paper_count": len(arxiv_papers),
            "total_pdf_count": len(pdf_files),
            "arxiv_papers": arxiv_papers,
            "recommended_tool": "arxiv_rename_papers"
            if len(arxiv_papers) > 0
            else None,
        }
    )


@mcp.tool()
def arxiv_search_papers(query: str, max_results: int = 10) -> str:
    """
    Search for scientific papers on arXiv.org

    Args:
        query: The search query for scientific papers
        max_results: Maximum number of papers to return (default: 10)

    Returns:
        JSON string with academic paper search results
    """
    if not query:
        return json.dumps({"error": "Query parameter is required"})

    # Use the arXiv API to search for papers
    search = arxiv.Search(
        query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )

    results = []
    for paper in search.results():
        results.append(
            {
                "id": paper.entry_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary[:300] + "..."
                if len(paper.summary) > 300
                else paper.summary,
                "published": paper.published.strftime("%Y-%m-%d"),
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
            }
        )

    return json.dumps({"results": results}, indent=2)


@mcp.tool()
def arxiv_download_paper(arxiv_id: str, rename: bool = True) -> str:
    """
    Download a scientific paper from arXiv.org by its ID

    Args:
        arxiv_id: The arXiv ID of the paper (e.g., 2101.12345)
        rename: Whether to rename the paper based on its title (default: True)

    Returns:
        JSON string with download status
    """
    if not arxiv_id:
        return json.dumps({"error": "arXiv ID is required"})

    # Clean the ID (sometimes it comes with the arxiv.org prefix)
    if "/" in arxiv_id and "arxiv.org" in arxiv_id:
        arxiv_id = arxiv_id.split("/")[-1]

    try:
        # Get the paper by ID
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        # Create a filename from the title if rename=True, otherwise use arXiv ID
        if rename:
            # Use the new naming format: arxiv_{id}_{title}.pdf
            safe_title = sanitize_filename(paper.title)
            # Replace / with _ in arxiv_id for filename compatibility
            safe_id = arxiv_id.replace("/", "_")
            filename = f"arxiv_{safe_id}_{safe_title}.pdf"
        else:
            filename = f"arXiv_{arxiv_id.replace('/', '_')}.pdf"

        filepath = os.path.join(PAPERS_DIR, filename)

        # Download the PDF
        paper.download_pdf(filepath=filepath)

        return json.dumps(
            {
                "success": True,
                "message": f"Paper downloaded successfully",
                "filename": filename,
                "path": filepath,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "categories": paper.categories,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def arxiv_rename_papers(
    papers_dir: str = None, arxiv_id: str = None, file_path: str = None
) -> str:
    """
    Rename arXiv papers based on their titles

    Args:
        papers_dir: Directory containing arXiv papers to rename
        arxiv_id: Specific arXiv ID to rename (requires file_path)
        file_path: Path to the specific paper file to rename

    Returns:
        JSON string with renaming results
    """
    # Expand ~ to home directory if present in paths
    if papers_dir and papers_dir.startswith("~"):
        papers_dir = os.path.expanduser(papers_dir)

    if file_path and file_path.startswith("~"):
        file_path = os.path.expanduser(file_path)

    # Handle single file renaming
    if arxiv_id and file_path:
        try:
            logger.info(f"Renaming single file: {file_path} with ID {arxiv_id}")

            # Clean the ID (sometimes it comes with the arxiv.org prefix)
            if "/" in arxiv_id and "arxiv.org" in arxiv_id:
                arxiv_id = arxiv_id.split("/")[-1]

            # Get the paper by ID
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(search.results())

            # Create a new filename using the format arxiv_{id}_{title}.pdf
            safe_title = sanitize_filename(paper.title)
            safe_id = arxiv_id.replace("/", "_")
            new_filename = f"arxiv_{safe_id}_{safe_title}.pdf"

            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_filename)

            # Rename the file
            shutil.copy(file_path, new_path)

            return json.dumps(
                {
                    "success": True,
                    "message": f"Paper renamed successfully",
                    "original_path": file_path,
                    "new_path": new_path,
                    "new_filename": new_filename,
                },
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error in rename_papers (single file): {e}")
            return json.dumps({"error": str(e)}, indent=2)

    # Handle batch renaming
    if papers_dir:
        # Use default directory if not specified
        if papers_dir == "default":
            papers_dir = PAPERS_DIR

        try:
            # Make sure the directory exists
            if not os.path.exists(papers_dir) or not os.path.isdir(papers_dir):
                return json.dumps(
                    {"success": False, "message": f"Directory not found: {papers_dir}"},
                    indent=2,
                )

            # Find all PDF files in the directory
            pdf_files = [
                f for f in os.listdir(papers_dir) if f.lower().endswith(".pdf")
            ]
            renamed_count = 0
            failed_count = 0
            renamed_papers = []

            for pdf_file in pdf_files:
                original_path = os.path.join(papers_dir, pdf_file)

                # Check if it's an arXiv paper
                if not is_arxiv_paper(pdf_file):
                    continue

                # Extract arXiv ID from filename
                arxiv_id = extract_arxiv_id(pdf_file)
                if not arxiv_id:
                    failed_count += 1
                    continue

                try:
                    # Get the paper by ID
                    search = arxiv.Search(id_list=[arxiv_id])
                    paper = next(search.results())

                    # Create a new filename using the format arxiv_{id}_{title}.pdf
                    safe_title = sanitize_filename(paper.title)
                    safe_id = arxiv_id.replace("/", "_")
                    new_filename = f"arxiv_{safe_id}_{safe_title}.pdf"

                    new_path = os.path.join(papers_dir, new_filename)

                    # Rename the file
                    shutil.copy(original_path, new_path)
                    renamed_count += 1
                    renamed_papers.append(new_filename)
                except Exception:
                    failed_count += 1

            return json.dumps(
                {
                    "success": renamed_count > 0,
                    "message": f"Renamed {renamed_count} papers, failed {failed_count}",
                    "renamed": renamed_count,
                    "failed": failed_count,
                    "renamed_papers": renamed_papers,
                },
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error in rename_papers (batch): {e}")
            return json.dumps({"error": str(e)}, indent=2)

    return json.dumps(
        {"error": "Either (arxiv_id and file_path) or papers_dir must be specified"},
        indent=2,
    )


# Prompts
@mcp.prompt()
def arxiv_search_prompt(query: str) -> str:
    """Create a prompt to search for scientific papers"""
    return f"""
    I'll search for scientific papers related to: {query}

    I'll use the arxiv_search_papers tool to find relevant papers on arXiv.org.
    After finding interesting papers, I can download them using the arxiv_download_paper tool.
    """


@mcp.prompt()
def arxiv_process_directory(directory_path: str = "~/Downloads") -> str:
    """
    Create a prompt to process a directory of arXiv papers
    """
    return f"""
    I'll help you organize arXiv papers in {directory_path}.

    First, I'll use the arxiv_detect_directory tool to check for arXiv papers.
    Then, I'll use the arxiv_rename_papers tool to rename any papers I find based on their titles.

    Let me start by checking the directory for arXiv papers...
    """


# Root endpoint handler
async def root_handler(request: Request) -> Response:
    """Handle requests to the root endpoint"""
    return JSONResponse(
        content={"status": "ok", "message": "arXiv Helper API is running"}, 
        status_code=200
    )


def parse_args():
    parser = argparse.ArgumentParser(description="arXiv Helper MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mechanism to use (stdio or sse)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind SSE server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port to bind SSE server to (default: 3001)",
    )
    return parser.parse_args()


def create_starlette_app(mcp_server):
    """Create a Starlette application with SSE transport."""
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

    # Create base app first with root endpoint
    app = Starlette(
        routes=[
            Route("/", endpoint=root_handler, methods=["GET"]),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )

    # Then add middleware to the app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Run the server if executed directly
if __name__ == "__main__":
    args = parse_args()

    # Use the custom Starlette app for SSE transport
    if args.transport == "sse":
        mcp_server = mcp._mcp_server
        app = create_starlette_app(mcp_server)
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
