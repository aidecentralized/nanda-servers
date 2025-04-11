# SDG MCP (Synthetic Data Generation - Model Context Protocol)

A Python-based tool for generating synthetic data using CTGAN (Conditional Tabular GAN) with an interactive MCP client-server architecture.

## Features

- **Synthetic Data Generation**: Generate synthetic tabular data using CTGAN models
- **Interactive Client-Server Architecture**: Built using FastMCP for seamless communication
- **Data Analysis Tools**: 
  - Read and analyze CSV file schemas
  - View top records from datasets
  - Execute custom Python scripts
  - Generate synthetic data with configurable parameters

## Prerequisites

- Python 3.10 or higher
- Required Python packages (automatically installed via dependencies):
  - anthropic >= 0.49.0
  - fastmcp >= 0.4.1
  - mcp[cli] >= 1.6.0
  - pandas >= 2.2.3
  - sdv[tabular] >= 1.19.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SDG_MCP.git
cd SDG_MCP
```

2. Install dependencies:
```bash
pip install -e .
```

3. Export Anthropic Api Key

```
export ANTHROPIC_API_KEY=<your_api_key>
```
## Usage

### Starting the Server

Run the server using:
```
uv run client.py server.py

```

### Using the Client

Run the client with:
```bash
python client.py server.py
```

The client provides an interactive interface where you can:
- Generate synthetic data from CSV files
- Analyze data schemas
- View sample records
- Execute custom Python scripts

## Available Tools

1. **read_schema(FilePath)**: Returns the schema of a CSV file
2. **read_top_5_reccords(FilePath)**: Displays the first 5 records of a CSV file
3. **execute_python_script(script)**: Executes custom Python code
4. **generate_synthetic_data_from_gan(FilePath)**: Generates synthetic data using CTGAN

## Project Structure

- `server.py`: Contains the MCP server implementation and tool definitions
- `client.py`: Implements the interactive client with Claude AI integration
- `main.py`: Entry point for the application
- `pyproject.toml`: Project configuration and dependencies
