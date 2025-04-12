# Compare-Zipcodes MCP Server
---
A FastMCP-compatible **Model Context Protocol (MCP)** server for comparing zipcode-level demographic distributions. It includes a tool for detecting statistically significant differences in population segments—based on age, gender, and ethnicity—between two ZIP Code Tabulation Areas (ZCTAs), using z-score analysis over synthetic census data. 

This repository also includes instructions on how to integrate the MCP server with Claude Desktop.

## Features

- Compares zip code demographics based on `age` x `gender` x `ethnicity` using Z-score based anomaly detection
- Synthetic population and household census data integration via `.pkl` files generated from [AgentTorch](https://github.com/AgentTorch/AgentTorch)

---

## Installation

```bash
git clone https://github.com/anna8murphy/mcp-compare-zipcodes.git
cd mcp-compare-zipcodes
```

```bash
# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# set up environment
uv venv
source .venv/bin/activate
uv add "mcp[cli]" httpx
```

## Start the server

Run the server:

```bash
uv run compare-zipcodes.py
```

Running the server will make the `compare_regions` tool available, which returns a summary of statistically significant demographic differences (z-score > 2) between two ZIP codes based on age, gender, and ethnicity groupings.

## Usage on Claude Desktop
Open the Claude for Desktop App configuration in a text editor: 

`~/Library/Application\ Support/Claude/claude_desktop_config.json`

Add the server:
```bash
{
    "mcpServers": {
        "mcp-compare-zipcodes": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp-compare-zipcodes",
                "run",
                "compare-zipcodes.py"
            ]
        }
    }
}
```

**Example Prompt:** Compare the demographic statistics of the following zipcodes: 02139 and 10036.

### Project Structure
```plaintext
mcp-compare-zipcodes/
├── README.md              # documentation
├── compare-zipcodes.py    # main script for Claude integration
├── server.py              # MCP server implementation
├── pyproject.toml         # Python project configuration
└── uv.lock                # uv package manager lock file

