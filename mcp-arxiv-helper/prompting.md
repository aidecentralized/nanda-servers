# How to Effectively Prompt Claude with arXiv MCP

## Common Issues

Claude Desktop sometimes doesn't automatically use available MCP tools when discussing arXiv papers. This guide will help you prompt Claude effectively to use the arXiv Paper Assistant.

## Effective Prompting Techniques

### 1. Be Explicit About Using Tools

**Instead of:**
```
Find me papers about quantum computing
```

**Try:**
```
Please use the search_papers tool to find recent papers about quantum computing
```

### 2. Use Specific Keywords

Always include these trigger words:
- "arXiv"
- "papers" or "scientific papers"
- Tool names: "search_papers", "download_paper", "rename_papers"

### 3. Multi-Step Instructions

Break down complex tasks:

```
I need help with arXiv papers. First, use the search_papers tool to search for "graph neural networks". Then, help me pick the most relevant one and download it using the download_paper tool.
```

### 4. Paper Processing Templates

For processing existing papers:

```
I have arXiv papers in ~/Downloads. Please:
1. Use the detect_arxiv_directory tool to check for arXiv papers
2. Use the rename_papers tool to rename them based on their titles
```

### 5. Restarting if Claude Gets Stuck

If Claude isn't using the tools properly:

```
Let's start over. You have access to arXiv paper tools. Please use the search_papers tool to look for [topic].
```

### 6. Sample Workflows

#### Research Overview:
```
I'm researching [topic]. Please use the arXiv MCP tools to:
1. Search for 5 recent papers on this topic
2. Show me their abstracts
3. Download the most promising one
```

#### Paper Organization:
```
I need to organize my arXiv papers in [directory]. Please:
1. Detect if there are arXiv papers using the detection tool
2. Rename any papers with cryptic filenames using the rename_papers tool
```

## Debugging Tips

If Claude ignores the MCP functionality:
1. Check that Claude Desktop shows the MCP server as connected
2. Restart the conversation
3. Be very explicit about using the tools by name
4. If all else fails, try restarting Claude Desktop

Remember: The more specific your instructions about using the tools, the better Claude will perform!
