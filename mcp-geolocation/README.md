# Geo MCP Server 🌍

This is a [Model Context Protocol (MCP)](https://modelcontextprotocol.org) compatible server that provides **IP-based geolocation** services using the **IP-API**.

It enables AI models or agents to call a simple tool and retrieve location data such as city, region, country, latitude, longitude, timezone, ISP, and more.

---

## 🛠️ Tool: `geolocate` 🧭

```python
geolocate(ip: str) → dict
Returns geolocation information for the provided IP address.

Example Input:

{ "ip": "8.8.8.8" }

Example Output:

{
  "ip": "8.8.8.8",
  "city": "Mountain View",
  "region": "California",
  "country": "United States",
  "lat": 37.386,
  "lon": -122.0838,
  "timezone": "America/Los_Angeles",
  "isp": "Google LLC",
  "as": "AS15169 Google LLC"
}
```

## ⚙️ Setup

### 1. Install dependencies:
```
npm install
```

### 2. Run the server:

```
npm start
```

### 3. Connect via MCP client: Configure your MCP-compatible client (e.g., Claude Desktop) to connect to this server.

## 📦 Features

🌐 IP geolocation using IP-API

🔑 No API key required

📉 Rate-limited to 45 requests per minute

🧾 Clean, structured JSON responses

🧩 Plug-and-play with Claude Desktop and other MCP clients


## 📦 Tech Stack

Python 3.9+

MCP Python SDK

IP-API.com (no key required)

 ## 🧰 Setup

 ```
 git clone https://github.com/yourusername/geo-mcp-server.git
cd geo-mcp-server
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run src/geo/server.py
```

## 🗺️ License
MIT — free to use, modify, and share.

