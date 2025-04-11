from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import json

# Initialize FastMCP server with a name
mcp = FastMCP("MemoryBankHelper")

# Templates for Memory Bank files
TEMPLATES = {
    "projectbrief.md": """# Project Brief: [Project Name]

## Overview
[High-level overview of what you're building]

## Core Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

## Goals
- [Goal 1]
- [Goal 2]
- [Goal 3]

## Project Scope
[Define what is in and out of scope for this project]""",

    "productContext.md": """# Product Context: [Project Name]

## Problem Statement
[Describe the problem this project solves]

## User Experience Goals
- [UX Goal 1]
- [UX Goal 2]
- [UX Goal 3]

## Success Metrics
- [Metric 1]
- [Metric 2]
- [Metric 3]""",

    "activeContext.md": """# Active Context: [Project Name]

## Current Work Focus
[Describe what you're currently working on]

## Recent Changes
- [Change 1]
- [Change 2]
- [Change 3]

## Next Steps
- [Step 1]
- [Step 2]
- [Step 3]

## Active Decisions and Considerations
[Document decisions being made and factors being considered]

## Important Patterns and Preferences
[Document patterns that are emerging in the project]

## Learnings and Project Insights
[Document what you've learned so far]""",

    "systemPatterns.md": """# System Patterns: [Project Name]

## System Architecture
[Describe the overall architecture]

## Key Technical Decisions
- [Decision 1]
- [Decision 2]
- [Decision 3]

## Design Patterns in Use
- [Pattern 1]
- [Pattern 2]
- [Pattern 3]

## Component Relationships
[Describe how components interact]

## Critical Implementation Paths
[Describe critical paths in the implementation]""",

    "techContext.md": """# Tech Context: [Project Name]

## Technologies Used
- [Technology 1]
- [Technology 2]
- [Technology 3]

## Development Setup
[Describe the development environment setup]

## Technical Constraints
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

## Dependencies
- [Dependency 1]
- [Dependency 2]
- [Dependency 3]

## Tool Usage Patterns
[Describe how tools are used in the project]""",

    "progress.md": """# Progress: [Project Name]

## What Works
- [Feature 1]
- [Feature 2]
- [Feature 3]

## What's Left to Build
- [Feature 4]
- [Feature 5]
- [Feature 6]

## Known Issues and Limitations
- [Issue 1]
- [Issue 2]
- [Issue 3]

## Evolution of Project Decisions
[Document how project decisions have evolved]"""
}

# Guide content for Memory Bank
GUIDES = {
    "setup": """## Setting Up Memory Bank

1. Create a 'memory-bank/' directory in your project
2. Create the core files using our templates
3. Fill in the details based on your project
4. Update regularly as your project evolves

The Memory Bank is a living documentation system that helps maintain context across sessions.""",

    "usage": """## Using Memory Bank

Memory Bank updates occur when:
1. Discovering new project patterns
2. After implementing significant changes
3. When user requests with **update memory bank** (MUST review ALL files)
4. When context needs clarification

Remember: After every memory reset, begin by reading the Memory Bank files to rebuild context.""",

    "benefits": """## Benefits of Memory Bank

- **Context Preservation**: Maintain project knowledge across sessions
- **Consistent Development**: Experience predictable interactions
- **Self-Documenting Projects**: Create valuable project documentation as a side effect
- **Scalable to Any Project**: Works with projects of any size or complexity
- **Technology Agnostic**: Functions with any tech stack or language""",

    "structure": """## Memory Bank Structure

The Memory Bank consists of core files and optional context files, all in Markdown format:

### Core Files (Required)
1. 'projectbrief.md' - Foundation document that shapes all other files
2. 'productContext.md' - Explains why the project exists, problems being solved
3. 'activeContext.md' - Current work focus, recent changes, next steps
4. 'systemPatterns.md' - System architecture, technical decisions, design patterns
5. 'techContext.md' - Technologies used, development setup, constraints
6. 'progress.md' - What works, what's left to build

### Additional Context
Create additional files/folders within memory-bank/ when they help organize:
- Complex feature documentation
- Integration specifications
- API documentation
- Testing strategies
- Deployment procedures"""
}

# Define a tool to get Memory Bank structure
@mcp.tool()
async def get_memory_bank_structure() -> str:
    """Get a detailed description of the Memory Bank file structure."""
    return GUIDES["structure"]

# Define a tool to generate Memory Bank template
@mcp.tool()
async def generate_memory_bank_template(file_name: str) -> str:
    """Generate a template for a specific Memory Bank file.
    
    Args:
        file_name: The name of the file to generate a template for (e.g., "projectbrief.md")
    """
    if file_name in TEMPLATES:
        return TEMPLATES[file_name]
    else:
        available_templates = ", ".join(TEMPLATES.keys())
        return f"Template for {file_name} not found. Available templates: {available_templates}"

# Define a tool to analyze project summary
@mcp.tool()
async def analyze_project_summary(project_summary: str) -> str:
    """Analyze a project summary and provide suggestions for Memory Bank content.
    
    Args:
        project_summary: A summary of the project
    """
    # In a real implementation, this would use more sophisticated analysis
    # For now, we'll provide generic suggestions with some basic extraction
    
    # Extract potential project name (first few words)
    words = project_summary.split()
    potential_name = " ".join(words[:3]) if len(words) >= 3 else project_summary
    
    # Extract potential technologies (look for common tech terms)
    tech_terms = ['React', 'Angular', 'Vue', 'Node', 'Python', 'Java', 'TypeScript', 
                 'JavaScript', 'HTML', 'CSS', 'API', 'REST', 'GraphQL', 'MongoDB', 
                 'SQL', 'PostgreSQL', 'MySQL', 'Docker', 'Kubernetes', 'AWS', 'Azure']
    
    found_tech = []
    for term in tech_terms:
        if term.lower() in project_summary.lower():
            found_tech.append(term)
    
    tech_section = ""
    if found_tech:
        tech_section = f"""## Tech Context
- Technologies identified: {', '.join(found_tech)}
- Consider documenting your development setup
- Note any technical constraints you're working with"""
    
    return f"""Based on your project summary, here are suggestions for your Memory Bank:

## Project Brief
- Project Name: Consider "{potential_name}..." or something more descriptive
- Include the core purpose from your summary
- Define key requirements based on the functionality mentioned
- Set clear goals derived from your project objectives

## Product Context
- Address the problem your project aims to solve
- Define user experience goals based on your target audience
- Consider success metrics that align with your project goals

{tech_section}

## System Patterns
- Consider appropriate architectural patterns for your project type
- Document key technical decisions as you make them
- Map out component relationships early

To get started:
1. Create a 'memory-bank/' directory in your project
2. Create the core files using our templates
3. Fill in the details based on these suggestions
4. Update regularly as your project evolves"""

# Add a resource for Memory Bank guide
@mcp.resource("memory_bank_guide://{section}")
async def memory_bank_guide(section: str) -> tuple[str, str]:
    """Provide guidance on Memory Bank setup and usage.
    
    Args:
        section: The section of the guide to retrieve
    """
    if section in GUIDES:
        content = f"# Memory Bank Guide: {section}\n\n{GUIDES[section]}"
        return content, "text/markdown"
    else:
        available_guides = ", ".join(GUIDES.keys())
        return f"Guide for {section} not found. Available guides: {available_guides}", "text/plain"

# HTML for the homepage
async def homepage(request: Request) -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memory Bank Helper</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            h1, h2, h3 { 
                color: #2c3e50;
            }
            .card {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            button:hover {
                background-color: #2980b9;
            }
            .status {
                border: 1px solid #ccc;
                padding: 10px;
                min-height: 20px;
                margin-top: 10px;
                border-radius: 4px;
                color: #555;
                background-color: #f5f5f5;
            }
            .tool-item {
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }
        </style>
    </head>
    <body>
        <h1>Memory Bank Helper</h1>
        
        <div class="card">
            <p>This MCP server helps you set up and maintain a Memory Bank for your projects. Memory Bank is a structured documentation system that allows AI assistants to maintain context across sessions.</p>
            <button id="connect-button">Connect to SSE</button>
            <div class="status" id="status">Connection status will appear here...</div>
        </div>
        
        <h2>Available Tools</h2>
        
        <div class="tool-item">
            <h3>get_memory_bank_structure</h3>
            <p>Returns a detailed description of the Memory Bank file structure.</p>
        </div>
        
        <div class="tool-item">
            <h3>generate_memory_bank_template</h3>
            <p>Returns a template for a specific Memory Bank file (e.g., "projectbrief.md").</p>
        </div>
        
        <div class="tool-item">
            <h3>analyze_project_summary</h3>
            <p>Analyzes your project summary and provides suggestions for Memory Bank content.</p>
        </div>
        
        <script>
            document.getElementById('connect-button').addEventListener('click', function() {
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
            Route("/", endpoint=homepage),  # Add the homepage route
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    mcp_server = mcp._mcp_server
    
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Memory Bank Helper MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()
    
    print(f"Starting Memory Bank Helper MCP Server on {args.host}:{args.port}")
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)