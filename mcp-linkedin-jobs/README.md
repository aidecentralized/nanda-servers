# TypeScript MCP Server (LinkedIn Job Tools)

This project provides a Model Context Protocol (MCP) server built with TypeScript and Node.js. It leverages the `@modelcontextprotocol/sdk` and uses a browser automation library to interact with LinkedIn. It allows MCP clients (like AI assistants or other applications) to search for LinkedIn job postings with various filters.


At j16z we are using it as part of Covercraft - to fetch information about job listings, companies, etc.

This MCP server is a part of [j16z](https://j16z.org)'s offering of MCP servers as an active collaborator of MIT's [Nanda registry](https://nanda.media.mit.edu/). The Nanda explorer can be found here: https://ui.nanda-registry.com/explorer


**Disclaimer:** Scraping LinkedIn can be against their Terms of Service and may require handling complex login procedures, CAPTCHAs, and rate limits. Use responsibly and ethically. This server likely requires an active LinkedIn session or credentials.

## Prerequisites

*   Node.js (v18 or later recommended)
*   npm (usually included with Node.js) or yarn

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd mcp-linkedin-jobs
    ```
    *(Replace `<your-repository-url>` with the actual URL)*

2.  **Install dependencies:**
    ```bash
    npm install
    ```


## Running Locally

1.  **Optional: Compile TypeScript (if needed, depending on setup):**
    *   Your `package.json` might have a build script:
        ```bash
        npm run build
        ```

2.  **Run the server:**
    *   Check your `package.json` for the appropriate run script.
        ```bash
        npm run dev
        pm2 start pnpm --name "mcp-linkedin" -- dev # if you are using pm2
        ```

    The server will start and listen for connections, typically on `http://localhost:3002` (or as configured). It uses Server-Sent Events (SSE) for communication.

## Testing Locally (Using `curl`)

You can test the running server using `curl` from your command line.

Ensure the server is running locally.
 Use `curl` to send requests to the `/tools/call` endpoint (adjust port if needed).
 ```
curl -I http://localhost:3002/linkedin-jobs
```

## Available Tools

The server exposes the following tool for MCP clients:

1.  **`linkedin-search`**
    *   **Description:** Searches for job postings on LinkedIn with various filters.
    *   **Arguments:**
        *   `keyword` (string, *optional*): Job title, skill, or company to search for.
        *   `location` (string, *optional*): Geographic area to search within (e.g., "London, United Kingdom", "Remote").
        *   `dateSincePosted` (enum, *optional*): Filter by date posted ("past month", "past week", "24hr").
        *   `jobType` (enum, *optional*): Type of job ("full time", "part time", "contract", "temporary", "volunteer", "internship").
        *   `remoteFilter` (enum, *optional*): Work location ("on site", "remote", "hybrid").
        *   `experienceLevel` (enum, *optional*): Experience level ("internship", "entry level", "associate", "senior", "director", "executive").
        *   `limit` (string, *optional*): Maximum number of job listings to return (default: "10").
        *   `page` (string, *optional*): Pagination page number (default: "0").
    *   **Example JSON Arguments:** `{ "keyword": "Product Manager", "location": "New York City", "limit": "5" }`

## Example Client Queries

An AI assistant integrated with this server could potentially handle requests like:

*   "Find the top 5 recent software engineer jobs in Austin, Texas on LinkedIn." (Uses `linkedin-search`)

## Deployment Guide

*(Deployment instructions specific to your chosen platform (e.g., AWS App Runner, Heroku, Google Cloud Run, Docker) would go here. This often involves containerizing the application with a `Dockerfile` and managing environment variables securely.)*

## Project Structure

*   `src/`: Contains the TypeScript source code (e.g., `index.ts`, tool implementations).
*   `node_modules/`: Directory where dependencies are installed.
*   `package.json`: Defines project metadata, dependencies, and scripts.
*   `package-lock.json`: Records exact dependency versions.
*   `tsconfig.json`: TypeScript compiler configuration.
*   `.env` / `.env.example`: Environment variable files (credentials, configuration).
*   `.gitignore`: Specifies intentionally untracked files for Git.
*   `README.md`: This file.
*   Potentially a `Dockerfile` for containerization.

## Technologies Used

*   Node.js
*   TypeScript
*   `@modelcontextprotocol/sdk` (Node.js MCP SDK)
*   Likely a browser automation library (e.g., `Puppeteer`, `Playwright`) for interacting with LinkedIn.
*   Potentially `Express.js` or another web framework for the server.
*   `dotenv` (for environment variables).
*   `npm` or `yarn` (Package managers).

## Notes

*   Interacting with LinkedIn programmatically is complex and requires careful handling of authentication, session management, rate limits, and potential UI changes.
*   Ensure compliance with LinkedIn's Terms of Service. Automated access might be restricted or lead to account issues.
*   Handle user credentials securely. Avoid hardcoding them in the source code. Use environment variables (`.env`) or a secrets management system.
*   Error handling is crucial, especially for dealing with login failures, CAPTCHAs, or unexpected page structures.
