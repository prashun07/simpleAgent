# Enterprise Knowledge Assistant

A production-style **RAG agent** that answers questions from your company documents.  
Designed for **open-source models** with flexible **local (Ollama)** or **cloud (Gemini/Groq)** execution.

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         .env configuration          │
                    │  LLM_PROVIDER / EMBEDDING_PROVIDER  │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
    ┌─────▼─────┐              ┌──────▼──────┐             ┌──────▼──────┐
    │  Ollama   │              │   Gemini    │             │    Groq     │
    │  (local)  │              │   (cloud)   │             │   (cloud)   │
    │ llama3.2  │              │ gemini-flash│             │ llama-3.3   │
    │ nomic-emb │              │ gemini-emb  │             │  (LLM only) │
    └─────┬─────┘              └──────┬──────┘             └──────┬──────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │   Enterprise Knowledge Assistant    │
                    │  Index → Retrieve → Augment → Gen   │
                    └─────────────────┬───────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
      data/documents/           chroma_db/              Answer + Citations
      (.txt .md .pdf)
```

## Project Structure

```
simpleAgent/
├── main.py                    # CLI (chat, index, info)
├── api/server.py              # FastAPI REST API
├── config/
│   ├── settings.py            # Load config from .env
│   └── providers.py           # LLM + embedding factories
├── knowledge/
│   ├── loader.py              # Load txt/md/pdf documents
│   └── indexer.py             # Chunk + store in Chroma
├── assistant/
│   └── agent.py               # RAG pipeline with citations
├── data/documents/            # Your knowledge base files
├── chroma_db/                 # Persistent vector store (auto-created)
├── .env.example               # Config template with presets
└── docker-compose.yml         # Optional Ollama container
```

## Quick Start

### 1. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys and provider choice
```

### 2. Add documents

Put your files in `data/documents/` (`.txt`, `.md`, `.pdf`).

A sample file is included: `data/documents/company_knowledge.md`

### 3. Run

```bash
# Check active providers
python main.py info

# Index documents
python main.py index --rebuild

# Start chat
python main.py
```

## Model Provider Presets

Switch providers in `.env` — no code changes needed.

### Preset 1: Fully local (open-source, private)

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

```bash
# Start Ollama (install from https://ollama.com or use docker-compose)
docker compose up -d ollama
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Preset 2: Hybrid — local embeddings + Groq LLM

Fast cloud inference with open-source Llama, local embedding search:

```env
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=ollama
GROQ_API_KEY=your-key
```

Get a free Groq key: https://console.groq.com

### Preset 3: All cloud Gemini (easiest)

```env
LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

Get a free Gemini key: https://aistudio.google.com/apikey

## CLI Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Interactive chat (auto-indexes if empty) |
| `python main.py index` | Index documents (skips if already indexed) |
| `python main.py index --rebuild` | Wipe and re-index all documents |
| `python main.py info` | Show active LLM and embedding providers |

In chat, type `reindex` to rebuild the index, `exit` to quit.

## REST API

```bash
uvicorn api.server:app --reload
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/config` | GET | Active model providers |
| `/index?rebuild=false` | POST | Index documents |
| `/ask` | POST | Ask a question |

Example:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What model providers are supported?"}'
```

## How RAG Works Here

1. **Index** — Documents are split into chunks and embedded into Chroma
2. **Retrieve** — Your question finds the top-K most similar chunks
3. **Augment** — Chunks are added to the prompt with source labels
4. **Generate** — The LLM answers using only that context
5. **Cite** — Sources are returned with relevance scores

## Open-Source Model Recommendations

| Role | Local (Ollama) | Cloud (Groq) |
|------|----------------|--------------|
| Fast chat | `llama3.2:3b` | `llama-3.1-8b-instant` |
| Better quality | `qwen2.5:7b` | `llama-3.3-70b-versatile` |
| Embeddings | `nomic-embed-text` | Use Ollama or Gemini |

## Legacy Files

| File | Purpose |
|------|---------|
| `rag_agent.py` | Original simple RAG tutorial (in-memory, Gemini only) |
| `agent.py` | Original rule-based agent |

## Next Steps for Your Portfolio

- [ ] Add PDF upload via API
- [ ] Add evaluation script with test Q&A pairs
- [ ] Add Langfuse tracing for observability
- [ ] Deploy with Docker + Render/Fly.io
- [ ] Add conversation memory for follow-up questions
