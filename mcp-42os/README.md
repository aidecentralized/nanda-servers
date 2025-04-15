# 🧠 42os — The Memory Layer for AI Agents

**Portable intelligence, built for the Internet of Agents.**

42os is a lightweight, developer-friendly memory layer that gives AI agents **persistent, programmable memory**—across platforms, sessions, and stacks. It's built for the [NANDA](https://nanda-registry.com/) protocol and designed to power portable, interoperable AI in a decentralized future.

> Most agents forget.  
> 42os remembers.

---

## 🌍 Why 42os?

As agents multiply across the Internet, they start from scratch every time:
- No memory of you
- No continuity
- No goals, no tone, no context

**42os fixes that.**  
It enables AI agents to **remember your history, persist knowledge, and share context** across ecosystems.

---

## ⚡️ Features

- 📦 **Portable Agent Memory**  
  Share and recall memory across NANDA-compliant agents.

- 🧠 **Semantic Search with FAISS**  
  Embed memories using Sentence Transformers and query with vector similarity.

- 🔄 **Programmable API**  
  Add, delete, query, and clear memories—via structured tools.

- 🗂 **Tagged, Timestamped Storage**  
  Each memory is contextualized with optional tags, timestamps, and sources.

- 🌐 **Built with FastMCP**  
  Fully compatible with [NANDA Inspector](https://inspector.nanda-registry.com) and Model Context Protocol.

---

## 🛠 Usage

### 🚀 Quickstart (Local)

```bash
git clone https://github.com/your-org/42os.git
cd 42os
pip install -r requirements.txt
python main.py
```

## 🧪 Test It Live with MCP Inspector

1. Run ```python main.py ```
2. In a new terminal run ``` npx @modelcontextprotocol/inspector ```
3. Configure to SSE and enter http://localhost:8080/sse
4. Try tools like ```store_memory```, ```query_memory```, and ```list_memories```

## 📁 Structure 

42os/
├── main.py              # FastMCP server with all tools
├── memory_store.json    # Disk persistence for memory
├── requirements.txt     # Python dependencies
└── README.md            # This file


## 🌐 NANDA Integration

42os is part of the NANDA ecosystem:

Works across NANDA-compliant agents and tools

Supports message routing via /messages/ and /sse

Enables cross-agent workflows, shared context, and modular memory handoff


🛡 License
MIT License.
Use it, build the memory web. 🌐

📬 Contact
Have an agent or product that needs memory?
Let’s collaborate → alyssamiataliotis@g.harvard.edu  p_shah@mit.edu
