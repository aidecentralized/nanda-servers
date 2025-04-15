from typing import Any
import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("ufmr")

# You can define global variables/constants here
ABOUT_RESPONSE = """
🩺 Thank you for your message!

**Tuberculosis (TB) Risk Factors:**
- Living or traveling in high-risk areas
- Close contact with infected individuals
- Weakened immune system (HIV/AIDS, malnutrition)
- Crowded or poorly ventilated living conditions

➡️ Early detection and treatment are key!
"""
@mcp.tool()
async def about_tb() -> str:
    """General awareness about TB"""
    return ABOUT_RESPONSE

@mcp.tool()
async def about_tb() -> str:
    """General awareness about TB"""
    return ABOUT_RESPONSE
if __name__ == "__main__":
    mcp.run(transport="sse")
