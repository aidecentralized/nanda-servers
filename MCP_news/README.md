# News API Service

A Python-based service that wraps [TheNewsAPI](https://thenewsapi.com/) to provide easy access to news articles via an MCP (Message Communication Protocol) server. This service allows you to fetch top news stories, all news articles, similar articles, and news sources with various filtering options.

## Features

- Fetch top news stories from around the world
- Search all news articles with advanced filtering
- Find similar news articles based on a specific article UUID
- Get news article details by UUID
- Browse available news sources with filtering options
- Server-Sent Events (SSE) support for real-time updates

## Prerequisites

- Python 3.7+
- News API key from [TheNewsAPI](https://thenewsapi.com/)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd news-api-service
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory with your News API key:
   ```
   NEWS_API_KEY=your_api_key_here
   ```

## Required Dependencies

- httpx - Used for async HTTP requests to the news API
- mcp - Message Communication Protocol server framework used throughout the application
- starlette - ASGI framework used for the web application
- uvicorn - ASGI server for running the application
- aiohttp - Async HTTP client/server framework
- python-dotenv - Used to load environment variables from a .env file
- requests - HTTP library for making requests

### Usage

### Starting the Server

Run the news.py file to start the MCP server:

```
python news.py --host 0.0.0.0 --port 8080
```

By default, the server runs on `0.0.0.0:8080`.

### Manual Testing with the MCP Inspector

The MCP Inspector is a command-line tool for testing MCP servers:

```bash
npx @modelcontextprotocol/inspector
```

Connect to your server:

```
> connect sse http://localhost:8080/sse
```
## Tools

The server exposes the following MCP tools. Reference for valid input and output [The News Api Documentation](https://www.thenewsapi.com/documentation)

### 1. Get Top News

```python
get_top_news(locale="", categories="", search="")
```

Fetches top news stories with optional filtering:
- `locale`(string **optional**): Comma-seperated list of the 2-letter ISO 3166-1 code of the country (default is all countries)
- `categories` (string **optional**): Comma-seperated list of category of news to fetch (general, science, sports, business, health, entertainment, tech, politics, food, travel)
- `search`(string **optional**): Keywords or a phrase to search for
- **Example:** get_top_news(locale="us",categories="business,sports")
  
### 2. Get All News

```python
get_all_news(categories="", language="", search="")
```

Find all live and historical articles with filtering options:
- `language`(string **optional**): Comma-separated list of languages to include (default is all)
- `categories`(string **optional**): Comma-seperated list of category of news to fetch (general, science, sports, business, health, entertainment, tech, politics, food, travel)
- `search`(string,**optional**): Keywords or a phrase to search for
- **Example:** get_all_news(language="en",categories= "sports")

### 3. Get Similar News

```python
get_similar_news(uuid="", categories="", language="")
```

Find similar stories to a specific article based on its UUID:
- `uuid`(string **required**): The unique identifier for an article in the system
- `language`(string **optional**): Comma-separated list of languages to include (default is all)
- `categories`(string **optional**): Comma-seperated list of category of news to fetch (general, science, sports, business, health, entertainment, tech, politics, food, travel)

### 4. Get News by UUID

```python
get_news_by_uuid(uuid="")
```

Find specific articles by UUID:
- `uuid` (string **required**): The unique identifier for an article in the system

### 5. Get News Sources

```python
get_news_sources(categories="", language="", exclude_categories="", page="")
```

Get sources to use in your news API requests:
- `categories`(string **optional**): Comma-seperated list of category of news to fetch (general, science, sports, business, health, entertainment, tech, politics, food, travel)
- `exclude_categories'(string **optional**): Comma-separated list of categories to exclude
- `language`(string **optional**): Comma-separated list of languages to include
- `page`(string **optional**): Used to paginate through the result set (default is 1)


## Tool Response 
Documentation and API Error Codes: - [TheNewsAPI](https://www.thenewsapi.com/documentation))

Meta:
- found: Number of articles found for the request.
- returned: Number of articles returned on current page. If less than the limit, there are no more results
- limit: Limit based on the limit parameter.
- page: Page number based on the page parameter.

Data:
- uuid: Unique identifier for an article in the system.
- title: Article title.
- description: The article meta description.
- keywords: The article meta keywords.
- snippet: The first 60 characters of the article body.
- url: The URL to the article.
- image_url: The URL to the article image.
- language: The language of the source.
- published_at: The datetime the article was published.
- source: The domain of the source.
- categories: Array of strings which the source is categorized as.
- relevance_score: Relevance score based on the search parameter. If the search parameter is not used, this is null.
- locale: Locale of the source.

## Web Interface

The service provides a simple web interface accessible at the root URL (e.g., `http://localhost:8080/`). From this interface, you can:

1. Verify that the server is running correctly
2. Connect to the SSE endpoint for real-time updates
3. Monitor connection status

## Development

### Code Structure

- MCP server setup using FastMCP
- API communication with TheNewsAPI
- Helper functions for formatting responses
- Starlette application for web interface and SSE

## Acknowledgements
- [Model Context Protocol](https://modelcontextprotocol.io/) 
- [NANDA: The Internet of AI Agents](https://nanda.media.mit.edu/)
- [TheNewsAPI](https://thenewsapi.com/)

## Contributors
- Angela Garabet
- Patrick DeKelly
