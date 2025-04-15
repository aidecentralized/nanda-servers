# main.py

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import HTMLResponse
from mcp.server import Server

import uvicorn
import datetime
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import os

mcp = FastMCP("42os-mcp")

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

# === Persistent storage config ===
MEMORY_FILE = "memory_store.json"

# In-memory store for demo
memory_store = []

def save_to_disk():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_store, f, indent=2)

def load_from_disk():
    global memory_store
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory_store = json.load(f)

# === Embedding + FAISS Setup ===
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")
dimension = 384  # for this model
index = faiss.IndexFlatL2(dimension)
vector_store_ids = []  # maps FAISS index -> memory_store index

def load_embeddings():
    for i, m in enumerate(memory_store):
        embedding = embedding_model.encode([m["content"]])
        index.add(np.array(embedding).astype("float32"))
        vector_store_ids.append(i)

# === MCP setup ===
mcp = FastMCP("memory-layer")

@mcp.tool()
async def store_memory(content: str, tags: list[str] = [], source: str = "unknown") -> str:
    """
    Store a memory with optional tags and source.
    """
    memory = {
        "content": content,
        "tags": tags,
        "source": source,
        "timestamp": datetime.datetime.now().isoformat()
    }
    memory_store.append(memory)

    # Embed + store in FAISS
    embedding = embedding_model.encode([content])
    index.add(np.array(embedding).astype("float32"))
    vector_store_ids.append(len(memory_store) - 1)

    save_to_disk()
    return f"Stored memory: {content[:50]}..."

@mcp.tool()
async def query_memory(prompt: str, top_k: int = 3, min_score: float = 0.0) -> list:
    """
    Semantic memory search using FAISS. Returns top_k matches above min_score.
    """
    if len(memory_store) == 0:
        return ["No memory available."]
    if index.ntotal == 0:
        return ["Memory index is empty."]

    embedding = embedding_model.encode([prompt])
    distances, indices = index.search(np.array(embedding).astype("float32"), top_k)

    results = []
    for score, i in zip(distances[0], indices[0]):
        if i < len(memory_store):
            similarity = 1 / (1 + score)  # L2 to similarity score
            if similarity >= min_score:
                memory = memory_store[vector_store_ids[i]]
                results.append(f"{memory['content']} (score: {similarity:.2f})")

    return results if results else ["No relevant memories found."]

@mcp.tool()
async def list_memories() -> list[str]:
    """List all stored memory summaries"""
    return [f"{i+1}. {m['content'][:50]}..." for i, m in enumerate(memory_store)]

@mcp.tool()
async def delete_memory(index: int) -> str:
    """Deletes a memory entry by its index in the list."""
    # Note: FAISS is not updated in this prototype
    try:
        deleted = memory_store.pop(index)
        save_to_disk()
        return f"Deleted memory: '{deleted['content'][:50]}...'"
    except IndexError:
        return f"No memory found at index {index}."

@mcp.tool()
async def clear_memory() -> str:
    """Clears all stored memories"""
    memory_store.clear()
    # Note: FAISS is not cleared in this prototype
    save_to_disk()
    return "Memory store cleared."

# SSE App
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
            Route("/", endpoint=homepage),  # Add the homepage route
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)
