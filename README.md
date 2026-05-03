# ai-news-curator

> A local MCP server that aggregates news and research from multiple sources, deduplicates noise, and builds a queryable personal knowledge base — conversationally accessible through any MCP-compatible AI client.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The Problem

Staying informed across multiple sources — Hacker News, arXiv, Reddit, technical blogs — means either spending hours reading or missing things that matter. Search engines optimise for popularity, not relevance to your specific interests. RSS readers dump everything on you without filtering.

The result: important signal buried in noise, and no way to ask "what happened in AI infrastructure this week?" and get a useful answer.

## What This Does

`ai-news-curator` runs as a local MCP server that:

- **Fetches** articles from multiple sources on a schedule (Hacker News, arXiv, NewsAPI, Reddit, arbitrary RSS feeds)
- **Deduplicates** semantically — the same story covered by five outlets appears once
- **Summarises** each article locally using Ollama (no API costs)
- **Indexes** everything into a local vector database (ChromaDB) for semantic search
- **Exposes** the knowledge base as MCP tools, so you can query it conversationally through Claude Desktop, Continue.dev, or any MCP-compatible client

The knowledge base grows continuously in the background. The longer it runs, the more useful it becomes.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Data Sources                      │
│  Hacker News · arXiv · NewsAPI · Reddit · RSS       │
└──────────────────────┬──────────────────────────────┘
                       │ fetch (scheduled, every 2h)
                       ▼
┌─────────────────────────────────────────────────────┐
│                 Ingestion Pipeline                  │
│                                                     │
│  Fetch → Normalise → Deduplicate → Summarise        │
│                          │              │           │
│                    (URL hash +    (Ollama, local)   │
│                   semantic sim)                     │
└──────────┬───────────────────────────┬──────────────┘
           │                           │
           ▼                           ▼
┌──────────────────┐       ┌───────────────────────┐
│     SQLite       │       │       ChromaDB         │
│                  │       │                        │
│ Article metadata │       │ Embeddings + chunks    │
│ Dedup index      │       │ Semantic search index  │
│ Ingestion log    │       │                        │
└──────────────────┘       └───────────────────────┘
           │                           │
           └─────────────┬─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   MCP Server                        │
│                                                     │
│  search_news · get_latest · get_trending_topics     │
│  compare_coverage · summarise_topic · health_check  │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (stdio)
                       ▼
┌─────────────────────────────────────────────────────┐
│                  MCP Client                         │
│         Continue.dev · Claude Desktop               │
└─────────────────────────────────────────────────────┘
```

All inference runs locally via Ollama. No data leaves your machine. No API costs during normal operation.

---

## Tech Stack

| Layer         | Technology                    | Notes                                 |
| ------------- | ----------------------------- | ------------------------------------- |
| MCP framework | `fastmcp`                     | Official Anthropic MCP Python SDK     |
| Local LLM     | Ollama + Llama 3.1            | Summarisation, zero cost              |
| Embeddings    | `nomic-embed-text` via Ollama | Local, no API needed                  |
| Vector DB     | ChromaDB                      | Persistent, no server required        |
| Relational DB | SQLite                        | Metadata, dedup index                 |
| HTTP client   | `httpx`                       | Async-friendly                        |
| Scheduling    | APScheduler                   | Lightweight, no Redis needed          |
| Validation    | Pydantic v2                   | Schema enforcement on all LLM outputs |
| Linting       | Ruff                          | Replaces flake8 + black + isort       |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Python package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Ollama](https://ollama.com) installed and running
- Node.js 18+ (for MCP Inspector during development)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/ai-news-curator
cd ai-news-curator

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Pull required Ollama models
ollama pull llama3.1
ollama pull nomic-embed-text

# Configure environment
cp .env.example .env
# Edit .env with your settings (NewsAPI key optional for now)
```

### Run the MCP Server

```bash
python src/server.py
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python src/server.py
```

Open `http://localhost:6274` to call tools directly from your browser.

### Connect to Continue.dev (VS Code)

Add to `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "ai-news-curator",
      "command": "python",
      "args": ["/absolute/path/to/ai-news-curator/src/server.py"]
    }
  ]
}
```

---

## MCP Tools

Once connected, you can ask your AI client things like:

- _"What are people talking about in AI this week?"_ → uses `get_trending_topics`
- _"Find everything about RAG and vector databases"_ → uses `search_news`
- _"How has the transformer architecture story been covered across sources?"_ → uses `compare_coverage`
- _"Give me a briefing on what happened in open source LLMs this month"_ → uses `summarise_topic`

---

## Configuration

All sources are configured in `config/sources.yaml` — adding a new RSS feed requires no code changes:

```yaml
sources:
  - type: rss
    name: "Your Favourite Blog"
    url: "https://example.com/feed.xml"
    topics: ["ai", "engineering"]
```

---

## Development

```bash
# Run tests
uv run pytest

# Run only fast tests (skip external API calls)
uv run pytest -m "not integration"

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

---

## Design Decisions

A few architectural choices worth noting for anyone reading the code:

**Why SQLite + ChromaDB instead of just ChromaDB?**
ChromaDB handles semantic search well but is a poor fit for structured queries like "give me all articles from the last 7 days" or "has this URL been ingested before". SQLite handles those cheaply. Each database does what it's good at.

**Why local embeddings instead of OpenAI's?**
The ingestion pipeline runs continuously. Using a cloud embedding API would accumulate costs over time and create a network dependency for a process that should run unattended. `nomic-embed-text` via Ollama produces excellent embeddings at zero marginal cost.

**Why dedup at two levels?**
URL hashing catches exact duplicates cheaply before any embedding happens. Semantic similarity catches the same story published at different URLs (syndication, reposts, multiple outlets covering the same announcement). Both checks together keep the knowledge base clean without being expensive.

---

## License

MIT
