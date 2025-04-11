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
pip install -r requirements.txt
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

## 🧰 Available Tools

1. **`read_schema(FilePath)`**  
   Returns the schema of a CSV file as a dictionary with column names and their data types.

2. **`read_top_5_reccords(FilePath)`**  
   Returns the top 5 rows from the given CSV file.

3. **`execute_python_script(script)`**  
   Executes a Python script (as a string) and returns `"Success"` or `"Failure: <error>"`.

4. **`generate_synthetic_data_from_gan(FilePath)`**  
   Trains a CTGAN model on tabular data and outputs a synthetic CSV file.

5. **`profile_data(FilePath)`**  
   Returns profiling stats for a dataset including:
   - Data type
   - Null count
   - Unique values
   - Min and max values (for numeric columns)

6. **`generate_fake_rows(columns, num_rows=10)`**  
   Generates fake rows using the `Faker` library for the provided column names.

7. **`balance_classes(FilePath, label_column, strategy='over')`**  
   Balances class distribution using:
   - Oversampling (default)
   - Undersampling  
   Saves the output to a CSV file.

8. **`generate_timegan_synthetic_data(real_data_path, sequence_length=24, epochs=500, batch_size=128, latent_dim=16)`**  
   Trains a TimeGAN model on time-series data and generates synthetic sequences saved as

## Project Structure

- `server.py`: Contains the MCP server implementation and tool definitions
- `requirements.txt`: Contains the requirements for running this project
- `customer-100-masked.csv`: Demo dataset for users
