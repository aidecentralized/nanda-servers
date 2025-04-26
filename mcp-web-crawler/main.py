import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.pipedrive.com/en/jobs/c399c10d-519f-4ca4-b165-d72e2a0d3b38-automation-quality-engineer",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())