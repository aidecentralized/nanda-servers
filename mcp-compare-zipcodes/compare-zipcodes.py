from typing import Any
import httpx
import tempfile
import pandas as pd
from mcp.server.fastmcp import FastMCP
import aiohttp
import asyncio
from scipy.stats import zscore

mcp = FastMCP("compare-zipcodes")

DATA_BASE_URL = "https://web.media.mit.edu/~almurph/censusdata/output_v2/household/"

async def get_state_from_zip(zip_code, api_key):
    url = f"https://api.api-ninjas.com/v1/zipcode?zip={zip_code}"
    headers = {"X-Api-Key": "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        return data[0].get('state', "State not found") if data else "State not found"
                    else:
                        return data.get('state', "State not found")
                else:
                    text = await response.text()
                    return f"Error: {response.status}, {text}"
    except Exception as e:
        return f"Error: {str(e)}"

async def make_request(url: str) -> dict[str, Any] | None:
    """Make a request to the synthetic census data server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
            if url.endswith('.pkl'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                return pd.read_pickle(tmp_path)
            
    except:
        raise Exception("Error fetching data from the server.")

@mcp.tool()
async def compare_regions(a: str, b: str) -> str:
    state_a = await get_state_from_zip(a, "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM")
    state_b = await get_state_from_zip(b, "8hTyCK/WoCiwTFkcYpWq4g==9LeDJJSl2ktj7EXM")

    df_a = await make_request(f"{DATA_BASE_URL}/{state_a}/{a}_household.pkl")
    df_b = await make_request(f"{DATA_BASE_URL}/{state_b}/{b}_household.pkl")

    if df_a is None or df_b is None:
        return "Error loading data for one or both regions."

    result = []

    group_cols = ['age', 'gender', 'ethnicity']

    agg_a = df_a.groupby(group_cols).size().rename("count_a")
    agg_b = df_b.groupby(group_cols).size().rename("count_b")

    combined = pd.concat([agg_a, agg_b], axis=1).fillna(0)
    combined["z_score"] = zscore(combined["count_a"] - combined["count_b"])

    significant_diffs = combined[combined["z_score"].abs() > 2]
    if not significant_diffs.empty:
        result.append("Significant demographic differences (z > 2):")
        for idx, row in significant_diffs.iterrows():
            result.append(f" - {idx}: z={row['z_score']:.2f}")
    else:
        result.append("No significant demographic differences found.")

    return "\n".join(result)

if __name__ == "__main__":
    mcp.run(transport='stdio')

