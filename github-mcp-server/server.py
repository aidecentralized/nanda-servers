#!/usr/bin/env python3
"""
GitHub Integration MCP Server for NANDA

Enables NANDA agents to interact with GitHub:
- Create issues
- Create pull requests  
- Search repositories
- Get repo info
- List issues/PRs
"""

from mcp.server.fastmcp import FastMCP
from github import Github
import os
from typing import Optional

# Initialize MCP server
mcp = FastMCP("github-integration")

# GitHub client (initialized with token)
github_client: Optional[Github] = None


def get_github_client() -> Github:
    """Get or create GitHub client"""
    global github_client
    if github_client is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        github_client = Github(token)
    return github_client


@mcp.tool()
def create_issue(
    repo_name: str,
    title: str,
    body: str,
    labels: Optional[str] = None
) -> dict:
    """
    Create a GitHub issue
    
    Args:
        repo_name: Repository in format "owner/repo"
        title: Issue title
        body: Issue description
        labels: Comma-separated labels (optional)
    
    Returns:
        Issue details including URL and number
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        
        # Parse labels if provided
        label_list = [l.strip() for l in labels.split(",")] if labels else []
        
        # Create issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=label_list
        )
        
        return {
            "success": True,
            "issue_number": issue.number,
            "url": issue.html_url,
            "state": issue.state
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_pull_request(
    repo_name: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main"
) -> dict:
    """
    Create a pull request
    
    Args:
        repo_name: Repository in format "owner/repo"
        title: PR title
        body: PR description
        head_branch: Branch with your changes
        base_branch: Target branch (default: main)
    
    Returns:
        PR details including URL and number
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        
        return {
            "success": True,
            "pr_number": pr.number,
            "url": pr.html_url,
            "state": pr.state
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_repositories(query: str, max_results: int = 10) -> dict:
    """
    Search GitHub repositories
    
    Args:
        query: Search query (e.g., "language:python stars:>1000")
        max_results: Maximum number of results (default: 10)
    
    Returns:
        List of repositories with details
    """
    try:
        client = get_github_client()
        repos = client.search_repositories(query=query)
        
        results = []
        for repo in repos[:max_results]:
            results.append({
                "name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "url": repo.html_url,
                "language": repo.language
            })
        
        return {
            "success": True,
            "count": len(results),
            "repositories": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_repository_info(repo_name: str) -> dict:
    """
    Get detailed repository information
    
    Args:
        repo_name: Repository in format "owner/repo"
    
    Returns:
        Repository details
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        
        return {
            "success": True,
            "name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "language": repo.language,
            "url": repo.html_url,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_issues(
    repo_name: str,
    state: str = "open",
    max_results: int = 10
) -> dict:
    """
    List repository issues
    
    Args:
        repo_name: Repository in format "owner/repo"
        state: Issue state (open, closed, all)
        max_results: Maximum number of results
    
    Returns:
        List of issues
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        issues = repo.get_issues(state=state)
        
        results = []
        for issue in issues[:max_results]:
            results.append({
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url,
                "created_at": issue.created_at.isoformat(),
                "user": issue.user.login
            })
        
        return {
            "success": True,
            "count": len(results),
            "issues": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_pull_requests(
    repo_name: str,
    state: str = "open",
    max_results: int = 10
) -> dict:
    """
    List repository pull requests
    
    Args:
        repo_name: Repository in format "owner/repo"
        state: PR state (open, closed, all)
        max_results: Maximum number of results
    
    Returns:
        List of pull requests
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        prs = repo.get_pulls(state=state)
        
        results = []
        for pr in prs[:max_results]:
            results.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat(),
                "user": pr.user.login,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref
            })
        
        return {
            "success": True,
            "count": len(results),
            "pull_requests": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_file_content(
    repo_name: str,
    file_path: str,
    branch: str = "main"
) -> dict:
    """
    Get file content from repository
    
    Args:
        repo_name: Repository in format "owner/repo"
        file_path: Path to file in repository
        branch: Branch name (default: main)
    
    Returns:
        File content
    """
    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)
        contents = repo.get_contents(file_path, ref=branch)
        
        return {
            "success": True,
            "path": file_path,
            "content": contents.decoded_content.decode('utf-8'),
            "size": contents.size,
            "sha": contents.sha
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Run the MCP server
    print("🚀 Starting GitHub Integration MCP Server")
    print("📌 Make sure GITHUB_TOKEN environment variable is set")
    print()
    mcp.run()
