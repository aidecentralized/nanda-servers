# MCP Setup Helper

This MCP server helps users set up and configure their AI assistant environments with three key components:

1. **Memory Bank** - A structured documentation system for context preservation (Currently Implemented)
2. **MCP Servers** - Custom server implementations for extended AI capabilities (Coming Soon)
3. **Rules** - Configuration settings for AI behavior and limitations (Coming Soon)

## Current Features (Memory Bank)

- Get detailed information about Memory Bank structure
- Generate templates for Memory Bank files
- Analyze project summaries and provide suggestions for Memory Bank content
- Access guides on Memory Bank setup and usage

### MCP Servers Recommender & Setup (In Progress)
### Rules Recommender (In Progress)

## Running the Server

You can run the server using the provided script:

```bash
./run.sh
```

Or manually:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The server will be available at http://localhost:8080/sse.

## MCP .json setup example 

```json
{
  "mcpServers": {
    "memory-bank": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

## Available Tools

### get_memory_bank_structure

Returns a detailed description of the Memory Bank file structure.

### generate_memory_bank_template

Returns a template for a specific Memory Bank file.

Example:
```json
{
  "file_name": "projectbrief.md"
}
```

### analyze_project_summary

Analyzes a project summary and provides suggestions for Memory Bank content.

Example:
```json
{
  "project_summary": "Building a React web app for inventory management with barcode scanning"
}
```

## Memory Bank Structure

The Memory Bank consists of core files and optional context files, all in Markdown format:

### Core Files (Required)

1. `projectbrief.md` - Foundation document that shapes all other files
2. `productContext.md` - Explains why the project exists, problems being solved
3. `activeContext.md` - Current work focus, recent changes, next steps
4. `systemPatterns.md` - System architecture, technical decisions, design patterns
5. `techContext.md` - Technologies used, development setup, constraints
6. `progress.md` - What works, what's left to build

### Additional Context

Create additional files/folders within memory-bank/ when they help organize:
- Complex feature documentation
- Integration specifications
- API documentation
- Testing strategies
- Deployment procedures

## Testing with MCP Inspector

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Connect to your server:

```
> connect sse http://localhost:8080/sse
```

List available tools:

```
> list tools
```

Call a tool:

```
> call get_memory_bank_structure
```