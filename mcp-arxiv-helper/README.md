# arXiv Helper User Guide

This guide explains how to use the arXiv Helper with Claude Desktop to easily manage your arXiv research papers.

## Setup

1. Install the required packages:
```bash
pip install "mcp[cli]" arxiv
```

2. Download `arxiv_helper.py` to your computer

3. Create a directory for your papers:
```bash
mkdir ~/arxiv_papers
```

4. Configure Claude Desktop to use the helper:
   - Open Claude Desktop's configuration file:
     - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   - Add this configuration:
   ```json
   {
     "mcpServers": {
       "arXiv Helper": {
         "command": "python",
         "args": [
           "/full/path/to/arxiv_helper.py"
         ],
         "env": {
           "PAPERS_DIR": "/full/path/to/arxiv_papers"
         }
       }
     }
   }
   ```

5. Restart Claude Desktop

## For Claude: How to Use arXiv Helper Tools

Claude, when you see this guide, please follow these explicit instructions:

### 1. Detecting arXiv Papers

```
To detect arXiv papers in a directory:
- ALWAYS use the arxiv_detect_directory tool with the directory path
- Example: arxiv_detect_directory("/Users/username/Downloads")
- This tool returns a list of found arXiv papers and other statistics
```

### 2. Renaming arXiv Papers

```
To rename arXiv papers with proper titles:
- ALWAYS use the arxiv_rename_papers tool
- For a whole directory: arxiv_rename_papers(papers_dir="/path/to/directory")
- For a single file: arxiv_rename_papers(file_path="/path/to/file.pdf", arxiv_id="2101.12345")
- This tool renames papers based on their titles from arXiv metadata
```

### 3. Searching for Papers

```
To search for papers on arXiv.org:
- ALWAYS use the arxiv_search_papers tool
- Example: arxiv_search_papers("transformer neural networks", max_results=5)
- This returns paper metadata including titles, authors, and summaries
```

### 4. Downloading Papers

```
To download papers from arXiv.org:
- ALWAYS use the arxiv_download_paper tool
- Example: arxiv_download_paper("2101.12345")
- This downloads the paper and optionally renames it based on its title
```

## For Users: Example Prompts

Here are example prompts to use with Claude:

### Process Papers in Downloads

```
Please use the arXiv Helper to check my Downloads folder for arXiv papers and rename them with proper titles.
```

### Search and Download Papers

```
Please use the arXiv Helper to search for recent papers about "quantum machine learning" and help me download the most relevant one.
```

### Rename Specific Paper

```
I have a paper at ~/Downloads/2103.12345.pdf. Can you use the arXiv Helper to rename it based on its title?
```

## Troubleshooting

If Claude is not using the arXiv Helper tools:

1. Be very explicit in your request. Instead of "organize my papers," say "use the arxiv_detect_directory tool to check my Downloads folder for arXiv papers"

2. If that doesn't work, try using one of the prompt templates:
   ```
   Please use the arxiv_process_directory prompt for my Downloads folder
   ```

3. Make sure the arXiv Helper is properly configured in Claude Desktop by checking the logs
