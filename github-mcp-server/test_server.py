#!/usr/bin/env python3
"""
Test script for GitHub MCP server
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Test functions (import from server)
from server import (
    get_repository_info,
    search_repositories,
    list_issues
)

def test_get_repo_info():
    """Test getting repo info"""
    print("🧪 Test: Get Repository Info")
    result = get_repository_info("torvalds/linux")
    print(f"Result: {result}")
    print()

def test_search_repos():
    """Test searching repositories"""
    print("🧪 Test: Search Repositories")
    result = search_repositories("language:python stars:>10000", max_results=3)
    print(f"Result: {result}")
    print()

def test_list_issues():
    """Test listing issues"""
    print("🧪 Test: List Issues")
    result = list_issues("microsoft/vscode", state="open", max_results=5)
    print(f"Result: {result}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("GitHub MCP Server Tests")
    print("=" * 50)
    print()
    
    # Check token
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not set in .env file")
        exit(1)
    
    print("✅ GITHUB_TOKEN found")
    print()
    
    # Run tests
    test_get_repo_info()
    test_search_repos()
    test_list_issues()
    
    print("=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
