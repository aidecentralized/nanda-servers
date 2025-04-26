from mcp.server.fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, DefaultMarkdownGenerator, PruningContentFilter
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, ContentTypeFilter, ContentRelevanceFilter
from typing import Dict, List, Optional
import asyncio
import logging
import re
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
# TO DO: For linkeding Job listing need more custom crawling strategy
# TODO: fix the more smarter crawling stuff so that we dont get rate limited
# For now if it is a public linkedin job listing, or a job listing from a company website, the crawler works
# TODO: For inded, and other job listing sites, the crawler needs to be smarter
class MCPToolManager:
    def __init__(self, name: str):
        self.mcp = FastMCP(name)
        self._register_tools()
        self._crawler = None

    async def _get_crawler(self):
        if self._crawler is None:
            self._crawler = AsyncWebCrawler()
        return self._crawler

    def _get_company_domain(self, job_url: str) -> Optional[str]:
        """Extract company domain from job board URLs or return None"""
        url = urlparse(job_url)
        domain = url.netloc.lower()
        path_parts = url.path.strip('/').split('/')

        # Common job board patterns with company info extraction
        patterns = {
            'greenhouse.io': {
                'pattern': r'greenhouse.io/(?:companies/)?([^/]+)',
                'transform': lambda x: self._validate_company_name(x)
            },
            'lever.co': {
                'pattern': r'lever.co/([^/]+)',
                'transform': lambda x: self._validate_company_name(x)
            },
            'linkedin.com': {
                'pattern': r'linkedin.com/company/([^/]+)',
                'transform': lambda x: self._validate_company_name(x)
            },
            'workday.com': {
                'pattern': r'workday.com/([^/]+)',
                'transform': lambda x: self._validate_company_name(x)
            },
            'wellfound.com': {
                'pattern': r'wellfound.com/company/([^/]+)',
                'transform': lambda x: self._handle_wellfound_company(x)
            }
        }

        def _handle_wellfound_company(self, company_name: str) -> Optional[str]:
            """Special handler for Wellfound company pages"""
            # If it's a known job board domain, try to get their actual domain
            known_job_boards = {
                'lever': 'lever.co',
                'greenhouse': 'greenhouse.io',
                'workday': 'workday.com'
            }

            if company_name in known_job_boards:
                return known_job_boards[company_name]

            # Otherwise assume it's a regular company
            return f"{company_name}.com"

        def _validate_company_name(self, name: str) -> Optional[str]:
            """Basic validation and cleaning of company names"""
            # Remove common suffixes and clean the name
            name = re.sub(r'[-_]', '', name.lower())

            # List of known job board names to avoid
            job_boards = {'lever', 'greenhouse', 'workday', 'jobs', 'careers', 'hire'}

            if name in job_boards:
                return None

            return f"{name}.com"

        # First check if we're already on a company domain
        if not any(board in domain for board in patterns.keys()):
            return domain

        # Check for job board patterns
        for board_domain, config in patterns.items():
            if board_domain in domain:
                if match := re.search(config['pattern'], job_url):
                    company_name = match.group(1)
                    return config['transform'](company_name)

        # If we're in a path like /company/xxx/jobs, try to extract
        if len(path_parts) >= 2 and 'company' in path_parts:
            company_idx = path_parts.index('company')
            if len(path_parts) > company_idx + 1:
                return self._validate_company_name(path_parts[company_idx + 1])

        return None

    def _register_tools(self):
        @self.mcp.tool()
        async def crawl_job_posting(url: str) -> Dict:
            """
            Crawl just the job posting page to get the job description
            """
            try:
                # Basic browser config
                browser_config = BrowserConfig(headless=True)

                # Use a session ID to maintain the session across requests
                session_id = "job_posting_session"

                # Configure the crawler run with enhanced content cleaning
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    excluded_tags=["nav", "footer", "aside"],
                    remove_overlay_elements=True,
                    markdown_generator=DefaultMarkdownGenerator(
                        options={
                            "ignore_links": False,  # Ignore links to focus on text content
                            "escape_html": True,  # Convert HTML entities to text
                            "body_width": 80  # Wrap text at 80 characters for readability
                        }
                    ),
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    session_id=session_id  # Use session ID
                )

                # Initialize the crawler if it doesn't exist
                if not hasattr(self, '_crawler') or self._crawler is None:
                    self._crawler = AsyncWebCrawler(config=browser_config)
                    await self._crawler.start()

                # Use the existing crawler instance
                result = await self._crawler.arun(url=url, config=crawler_config)

                if not result:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Failed to get any result from crawler"
                            }
                        ],
                        "isError": True
                    }

                if not result[0].markdown or not result[0].markdown.raw_markdown:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "No content found in the page"
                            }
                        ],
                        "isError": True
                    }

                # Get the markdown content from the result and ensure it's not empty
                content = str(result[0].markdown.raw_markdown).strip()
                if not content:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Page was crawled but no content was extracted"
                            }
                        ],
                        "isError": True
                    }

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ],
                    "isError": False
                }

            except Exception as e:
                logger.error(f"Error crawling job posting {url}: {e}")
                # Reset the crawler if there's a browser error
                if "browser has been closed" in str(e) or "Target page" in str(e):
                    try:
                        await self._crawler.close()
                    except:
                        pass
                    self._crawler = None
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error while crawling: {str(e)}"
                        }
                    ],
                    "isError": True
                }

        # @self.mcp.tool()
        # @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
        # async def crawl_company_context(url: str, max_depth: int = 1) -> Dict:
        #     """
        #     Deep crawl a company website to gather comprehensive context
        #     """
        #     try:
        #         # Basic browser config
        #         browser_config = BrowserConfig(headless=True)

        #         # Configure the deep crawl strategy
        #         scorer = KeywordRelevanceScorer(
        #             keywords=[
        #                 "company culture", "mission", "values", "benefits",
        #                 "team", "about us", "careers", "work life",
        #                 "diversity", "inclusion", "growth", "development"
        #             ],
        #             weight=0.7
        #         )

        #         filter_chain = FilterChain([
        #             ContentTypeFilter(allowed_types=["text/html"]),
        #             ContentRelevanceFilter(
        #                 query="company information culture values mission team",
        #                 threshold=0.3
        #             )
        #         ])

        #         config = CrawlerRunConfig(
        #             deep_crawl_strategy=BestFirstCrawlingStrategy(
        #                 max_depth=max_depth,  # Reduce depth to limit requests
        #                 include_external=False,
        #                 url_scorer=scorer,
        #                 filter_chain=filter_chain,
        #                 max_pages=5  # Limit the number of pages to reduce load
        #             ),
        #             scraping_strategy=LXMLWebScrapingStrategy(),
        #             verbose=True
        #         )

        #         # Create a new crawler instance for each request
        #         async with AsyncWebCrawler(config=browser_config) as crawler:
        #             results = []
        #             async for result in await crawler.arun(url, config=config):
        #                 page_info = {
        #                     "url": result.url,
        #                     "content": result.markdown,
        #                     "depth": result.metadata.get("depth", 0),
        #                     "score": result.metadata.get("score", 0),
        #                     "type": "company_context",
        #                     "success": result.success
        #                 }
        #                 results.append(page_info)

        #             return {
        #                 "company_url": url,
        #                 "pages": results,
        #                 "success": True
        #             }

        #     except Exception as e:
        #         logger.error(f"Error crawling company context {url}: {e}")
        #         return {"url": url, "error": str(e), "success": False}

        # @self.mcp.tool()
        # async def smart_crawl_job(job_url: str) -> Dict:
        #     """
        #     Smart crawl that handles both job board listings and company websites
        #     """
        #     # First, get the job posting
        #     job_info = await self.crawl_job_posting(job_url)

        #     # Try to find company website if it's a job board
        #     company_domain = self._get_company_domain(job_url)
        #     if company_domain:
        #         # If we found a company domain, crawl it
        #         company_url = f"https://www.{company_domain}"
        #         company_info = await self.crawl_company_context(company_url)
        #     else:
        #         # If it's already a company website, deep crawl from there
        #         company_info = await self.crawl_company_context(job_url)

        #     return {
        #         "job_info": job_info,
        #         "company_info": company_info,
        #         "success": job_info.get("success", False)
        #     }

        # @self.mcp.tool()
        # async def batch_smart_crawl_jobs(urls: List[str]) -> List[Dict]:
            """
            Smart crawl multiple job listings in parallel
            """
            tasks = [self.smart_crawl_job(url) for url in urls]
            return await asyncio.gather(*tasks)

    # if at all you need to register resources, do it so
    # def _register_resources(self):
    #     @self.mcp.resource("greeting://{name}")
    #     def get_greeting(name: str) -> str:
    #         return f"Hello, {name}!"

    @property
    def server(self):
        return self.mcp._mcp_server