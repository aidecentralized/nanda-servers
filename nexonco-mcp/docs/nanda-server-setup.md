# NANDA MCP Configuration Guide

## Overview

This guide explains how to configure [NANDA, The Internet of Agents](https://nanda.media.mit.edu/) Server to use the Nexonco MCP server. The Model Context Protocol (MCP) allows [NANDA Host](https://host.nanda-registry.com/) to interact with external AI models and tools. NANDA server must be launched with Server-Sent Events (SSE) transport.

## Configuration Steps

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (for Method 1)
- Docker (for Method 2)

### 1. Download or clone the `nexonco-mcp` GitHub repository

### 2. Build and Run `Nexonco` NANDA server

#### <b>Method 1</b>: Run with Docker (Recommended)

> Requires: Docker

1. **Build the image:**

   ```bash
   docker build -t nexonco-mcp .
   ```

2. **Run the container:**

   ```bash
   docker run -p 8080:8080 nexonco-mcp
   ```
   
#### <b>Method 2</b>: Run with `uv` 

> Requires: [`uv`](https://github.com/astral-sh/uv)

```bash
uv run nexonco/server.py --transport sse
```

### 3. Register `Nexonco` Server to NANDA-Host

- Go to [NANDA Host](https://host.nanda-registry.com/)
- Open `Settings > Nanda Servers > Add New Server`
- Fill the informations
  - Server ID: nexonco-local
  - Server Name: Nexonco
  - Server URL: 127.0.0.1:8080
- Add Server

### 4. Verify Setup

1. Test the connection by asking NANDA Host:
   `Find predictive evidence for colorectal cancer therapies involving KRAS mutations.`
