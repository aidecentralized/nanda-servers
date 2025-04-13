# Claude Desktop MCP Configuration Guide

## Overview

This guide explains how to configure Claude Desktop to use the Nexonco MCP server. The Model Context Protocol (MCP) allows Claude to interact with external AI models and tools. Claude Desktop MCP server must be launched with STDIO transport.

## Configuration Steps

### Prerequisites

- [uv](https://github.com/astral-sh/uv) 
- Python 3.11+
- Claude Desktop (for MCP integration)

### 1. Download or clone the `nexonco-mcp` GitHub repository

### 2. Locate Configuration File

The configuration file location depends on your operating system:

- **macOS**:
  ```
  ~/Library/Application Support/Claude/claude_desktop_config.json
  ```

- **Windows**:
  ```
  %APPDATA%\Claude\claude_desktop_config.json
  ```

- **Linux**:
  ```
  ~/.config/Claude/claude_desktop_config.json
  ```

### 3. Edit Configuration

1. Open the configuration file in a text editor
2. Add or update the mcpServers section:

```json
{
  "mcpServers": {
    "nexonco": {
        "command": "uv",
        "args": [
            "--directory",
            "/full/path/to/nexonco/nexonco",
            "run",
            "server.py"
        ]
    }
  }
}
```

### 4. Verify Setup

1. Save the configuration file
2. Restart Claude Desktop completely
3. Test the connection by asking Claude:
   `Find predictive evidence for colorectal cancer therapies involving KRAS mutations.`
