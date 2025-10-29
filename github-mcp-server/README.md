# GitHub Integration MCP Server

MCP server that enables NANDA agents to interact with GitHub.

## Features

- ✅ Create issues
- ✅ Create pull requests
- ✅ Search repositories
- ✅ Get repository info
- ✅ List issues/PRs
- ✅ Get file content

## Installation

```bash
pip install -r requirements.txt
```

## Setup

1. **Get GitHub Token**:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:org`
   - Copy token

2. **Configure**:
   ```bash
   cp .env.example .env
   # Edit .env and add your token
   ```

3. **Run**:
   ```bash
   python server.py
   ```

## Usage Examples

### Create an Issue
```python
# NANDA agent can call:
create_issue(
    repo_name="username/repo",
    title="Bug: Login not working",
    body="Description of the bug...",
    labels="bug,priority-high"
)
```

### Create Pull Request
```python
create_pull_request(
    repo_name="username/repo",
    title="Fix: Update authentication",
    body="This PR fixes...",
    head_branch="fix-auth",
    base_branch="main"
)
```

### Search Repositories
```python
search_repositories(
    query="language:python stars:>1000",
    max_results=5
)
```

### Get Repo Info
```python
get_repository_info(repo_name="torvalds/linux")
```

## Available Tools

| Tool | Description |
|------|-------------|
| `create_issue` | Create new issue |
| `create_pull_request` | Create new PR |
| `search_repositories` | Search GitHub repos |
| `get_repository_info` | Get repo details |
| `list_issues` | List repo issues |
| `list_pull_requests` | List repo PRs |
| `get_file_content` | Get file from repo |

## Integration with NANDA

Add to your NANDA agent:

```python
from nanda_adapter import NANDA

# Your agent can now use GitHub tools
nanda = NANDA(your_logic)
nanda.add_mcp_server("github-integration", "http://localhost:8000")
```

## Contributing to nanda-servers

Want to add this to NANDA catalog?

1. Fork: https://github.com/aidecentralized/nanda-servers
2. Add folder: `github-integration/`
3. Copy these files
4. Submit PR

## Security

- **Never commit your GitHub token**
- Use `.env` file (gitignored)
- Limit token scope
- Rotate tokens regularly

## Testing

```bash
# Test create issue
curl -X POST http://localhost:8000/tools/create_issue \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "your-username/test-repo",
    "title": "Test Issue",
    "body": "Created via MCP server"
  }'
```

## License

MIT
