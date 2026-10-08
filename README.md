# FinGraph

**A financial intelligence agent that answers multi-hop questions over S&P 500 SEC 10-K filings using Graph RAG.**

FinGraph combines a knowledge graph of corporate relationships with a LangGraph ReAct agent to answer questions that vector-only RAG systems can't — like *"How is Apple connected to Caterpillar?"* or *"What financial metrics does Amazon disclose?"*

---

## Why Graph RAG

Traditional RAG (vector search + LLM) works well when the answer lives in a single passage. It fails when the answer is a **path through facts**:

| Question | Vector RAG | Graph RAG |
|---|---|---|
| "What does Apple's 10-K say about tariffs?" | ✅ Works | ✅ Works |
| "How is Apple connected to Caterpillar?" | ❌ Can't traverse | ✅ Finds the path |
| "Which companies are affected by the same credit-rating risk?" | ❌ No structure | ✅ Multi-hop query |
| "Show me the top companies by relationship count" | ❌ No aggregation | ✅ Native Cypher |

FinGraph uses a **hybrid approach**: the agent decides whether to run a structured Cypher query, traverse a path between entities, or look up entity names — per question.

---

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Client     │─────▶│  FastAPI         │─────▶│  LangGraph      │
│  (curl,     │      │  /chat           │      │  ReAct Agent    │
│   Streamlit,│      │  /chat/stream    │      │                 │
│   web app)  │      │  /health         │      └────────┬────────┘
└─────────────┘      └──────────────────┘               │
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    │                   │                   │
                                    ▼                   ▼                   ▼
                            ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
                            │  Neo4j Aura  │    │  OpenRouter  │   │   Neo4j      │
                            │  (graph +    │    │  Nemotron 3  │   │   (memory:   │
                            │   documents) │    │  Super (LLM) │   │   User/Fact) │
                            └──────────────┘    └──────────────┘   └──────────────┘
```

**Agent tools:**
1. `search_entity` — fuzzy lookup for entity names
2. `run_cypher` — LLM writes and executes Cypher queries
3. `find_path` — shortest path between two entities (multi-hop)
4. `get_entity_relationships` — all outgoing relationships from an entity
5. `recall_memory` / `save_memory` — long-term user memory

---

## Data

FinGraph is built on **[FinReflectKG](https://huggingface.co/datasets/domyn/FinReflectKG)** — a knowledge graph extracted from **SEC 10-K filings of S&P 500 companies (2014–2024)**.

| Metric | Value |
|---|---|
| Full dataset | 17.5M triplets, 103 Parquet files |
| Currently loaded | 5 files (~850K rows) |
| Entities | ~11,700 |
| Relationships | ~205,000 |
| Tickers | 27 |

### Graph schema

**Nodes:**
- `(:Entity {name, type})` — type is `ORG`, `PERSON`, `FIN_METRIC`, `GPE`, etc.
- `(:Ticker {symbol})` — lowercase tickers (`aapl`, `amzn`, `cat`)
- `(:Document {chunk_id, text, ticker, year, source_file})` — filing chunks
- `(:User {id})` and `(:Fact {text})` — long-term memory

**Relationships:**
- `(:Entity)-[:RELATED_TO {type, start_date, end_date}]->(:Entity)` — raw predicates (`discloses`, `impacts`, `depends on`)
- `(:Entity)-[:MENTIONED_IN]->(:Document)` — co-occurrence in a filing chunk
- `(:Ticker)-[:HAS_ENTITY]->(:Entity)` — entities associated with a ticker

> **Important:** `RELATED_TO.type` contains *raw text predicates* extracted by the dataset's LLM pipeline — not curated business types like `SUPPLIES_TO`. The agent knows this and labels weak connections honestly.

---

## Quick start

### Prerequisites

- Python 3.11+
- A free [Neo4j Aura](https://console.neo4j.io) instance
- A free [OpenRouter](https://openrouter.ai) API key (for Nemotron 3 Super)
- A free [HuggingFace](https://huggingface.co/settings/tokens) token (for faster dataset download)

### Install

```bash
git clone <your-repo>
cd fingraph
uv sync
```

### Configure

Create `.env`:

```env
# Neo4j Aura
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# HuggingFace
HF_TOKEN=hf_xxxxx

# SEC EDGAR (for edgartools, optional)
SEC_IDENTITY=Your Name you@example.com
```

> **No quotes around values.** Passwords with `#`, `$`, or spaces need quoting.

### Load data

```bash
# Downloads FinReflectKG to HF cache (~1.67 GB, one-time)
uv run python scripts/download_dataset.py

# Loads first 5 files into Neo4j (~10 min)
uv run python scripts/load_graph.py
```

To load more files, edit `TEST_FILES` in `scripts/load_graph.py`. Set to `None` for all 103 files.

### Run the API

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the auto-generated API UI.

---

## Usage

### Non-streaming chat

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"How is Apple connected to Caterpillar?","user_id":"demo","session_id":"s1"}'
```

### Streaming (SSE)

```bash
curl -N -X POST http://127.0.0.1:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What financial metrics does Amazon disclose?","user_id":"demo","session_id":"s1"}'
```

Events:
```
event: tool
data: {"tool": "search_entity"}

event: token
data: {"content": "Amazon"}

event: done
data: {}
```

### Long-term memory

```bash
# Session 1: tell it a fact
curl -X POST http://127.0.0.1:8000/api/v1/chat/ \
  -d '{"message":"Remember that I own 100 shares of Apple.","user_id":"mohamed","session_id":"s1"}'

# Session 2: recall it
curl -X POST http://127.0.0.1:8000/api/v1/chat/ \
  -d '{"message":"What do you know about me?","user_id":"mohamed","session_id":"s2"}'
```

Memory persists across sessions because facts are written to Neo4j as `(:User)-[:KNOWS]->(:Fact)`.

---

## Example queries

These questions work well with the current graph:

| Question | What it exercises |
|---|---|
| "How is Apple connected to Caterpillar?" | `find_path` (multi-hop) |
| "What financial metrics does Amazon disclose?" | `run_cypher` scoped to ticker |
| "Show me the top 10 companies by relationship count." | Aggregate Cypher |
| "Which PERSON entities does Apple mention?" | Filtered query |
| "What does Comcast disclose about credit ratings?" | Predicate search |
| "Remember I'm interested in renewable energy stocks." | Memory write |

Questions the graph **can't** answer (the agent will say so):

- "Who supplies Apple?" — no `SUPPLIES_TO` edges
- "Who competes with Apple?" — no `COMPETES_WITH` edges
- "What is Apple's current stock price?" — no real-time data

---

## Project structure

```
fingraph/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── core/config.py             # Pydantic settings
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── chat.py            # /chat, /chat/stream
│   │       └── health.py          # /health
│   ├── agents/
│   │   ├── finance_agent.py       # LangGraph ReAct agent + system prompt
│   │   └── tools.py               # search_entity, run_cypher, find_path, etc.
│   ├── graph/
│   │   ├── connection.py          # Neo4j driver + LangChain wrapper
│   │   ├── constraints.py         # Indexes and uniqueness constraints
│   │   └── schema.py              # Node/relationship constants
│   ├── memory/
│   │   └── store.py               # User/Fact memory in Neo4j
│   ├── schemas/
│   │   └── chat.py                # Pydantic request/response models
│   └── services/
│       └── llm.py                 # OpenRouter LLM factory
├── scripts/
│   ├── download_dataset.py        # Pull FinReflectKG from HuggingFace
│   ├── load_graph.py              # Batch-load Parquet into Neo4j
│   └── test_agent.py              # CLI test harness
├── data/
│   └── finreflectkg/              # Downloaded Parquet files
├── .env
├── pyproject.toml
└── README.md
```

---

## Tech stack (all free tier)

| Layer | Tool | Why |
|---|---|---|
| **Graph database** | Neo4j Aura Free | 200K nodes / 400K relationships |
| **LLM** | OpenRouter — NVIDIA Nemotron 3 Super (`:free`) | Best free model for tool calling |
| **Embeddings** | Voyage AI `voyage-4` | Finance-tuned, 200M free tokens |
| **Agent framework** | LangGraph | ReAct loop + checkpointer |
| **API** | FastAPI + Uvicorn | Async, SSE streaming |
| **Dataset** | FinReflectKG (HuggingFace) | 17.5M pre-extracted triplets |
| **Windows SSL fix** | `truststore` | Uses OS cert store instead of certifi |

---

## Configuration

| Env var | Required | Purpose |
|---|---|---|
| `NEO4J_URI` | ✅ | `neo4j+s://` connection string |
| `NEO4J_USERNAME` | ✅ | Usually `neo4j` |
| `NEO4J_PASSWORD` | ✅ | No quotes |
| `NEO4J_DATABASE` | ✅ | Usually `neo4j` |
| `OPENROUTER_API_KEY` | ✅ | LLM access |
| `HF_TOKEN` | ⚠️ recommended | Faster dataset download |
| `SEC_IDENTITY` | optional | For `edgartools` ingestion |

---

## Limitations & honest notes

**Data shape.** `FinReflectKG` was extracted by an LLM pipeline from filing text. The `RELATED_TO.type` predicates (`impacts`, `discloses`, `depends on`) are textual assertions, not curated business relationships. The agent is instructed to label weak connections honestly (e.g., "co-mentioned in the same filing chunk") rather than presenting them as strong facts.

**Entity noise.** The dataset contains generic entities like "third party", "vendor", "tenant" that aren't real organizations. The system prompt excludes these from answers.

**Coverage.** Only 5 of 103 files are loaded (Neo4j Aura Free caps at 400K relationships). To load all S&P 500 filings, switch to a local Neo4j instance (Neo4j Desktop) with no node/relationship limits.

**No real-time data.** Everything comes from 10-K filings (2014–2024). No stock prices, no news, no market data.

**Free-tier rate limits.** OpenRouter's free tier is 50 requests/day (or 1,000/day with a one-time $10 credit). For heavy use, expect to wait or switch providers.

---

## Roadmap

- [x] Neo4j graph loaded from FinReflectKG
- [x] LangGraph ReAct agent with 6 tools
- [x] FastAPI + SSE streaming
- [x] Long-term memory via Neo4j `User`/`Fact` nodes
- [ ] Vector search tool (Voyage AI embeddings over filing text)
- [ ] Streamlit frontend
- [ ] Docker deployment
- [ ] Community detection + LLM summaries for global questions
- [ ] Clean supply-chain layer (custom `SUPPLIES_TO` / `COMPETES_WITH` extraction)

---

## License

Dataset: [CC-BY-NC-4.0](https://huggingface.co/datasets/domyn/FinReflectKG) — non-commercial use only.

Code: MIT.

---

## Acknowledgements

- [FinReflectKG](https://huggingface.co/datasets/domyn/FinReflectKG) by Dominik / domyn
- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [Neo4j](https://neo4j.com/) for the graph backend
- [OpenRouter](https://openrouter.ai/) and [NVIDIA](https://www.nvidia.com/) for free LLM access
