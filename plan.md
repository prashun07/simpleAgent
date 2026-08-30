# Enterprise Knowledge Assistant — Project Plan & Interview Guide

## 1. What Is This Project?

**Enterprise Knowledge Assistant (EKA)** is a production-style **RAG (Retrieval-Augmented Generation)** application that lets users ask natural-language questions about company documents and receive **grounded answers with source citations**.

It is designed as a **portfolio project** to demonstrate understanding of:
- Agentic AI fundamentals (retrieve → augment → generate)
- RAG architecture with persistent vector search
- Open-source and cloud LLM integration (Ollama / Gemini / Groq)
- Production engineering: API auth, observability, evaluation, config-driven design

**One-line pitch:**
> "A configurable RAG assistant that answers questions from internal documents using local open-source models (Ollama) or cloud APIs (Gemini/Groq), with persistent Chroma search, citation-backed responses, API authentication, structured tracing, and an automated eval suite."

---

## 2. Problem It Solves

Companies store knowledge in PDFs, markdown files, and internal docs. Employees waste time searching manually, and generic chatbots hallucinate because they don't know company-specific content.

**This project solves that by:**
1. Indexing company documents into a searchable vector database (Chroma)
2. Retrieving only the most relevant passages for each question
3. Asking the LLM to synthesize a natural-language answer from that context
4. Returning citations and trace IDs so users can verify answers and debug quality

---

## 3. Architecture Overview

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Retrieve   │────▶│  Vector Store    │◀────│  Embeddings │
│  (top-K)    │     │  (Chroma DB)     │     │ Ollama/Gemini│
└──────┬──────┘     └──────────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────────┐
│  Augment    │────▶│  Prompt + Context │
│  (RAG)      │     │  + Guardrails     │
└──────┬──────┘     └──────────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────────┐
│  Generate   │────▶│  Answer + Sources │
│  (LLM)      │     │  + trace_id       │
└─────────────┘     └──────────────────┘
       │
       ▼
┌─────────────┐
│  Observability │  logs/traces.jsonl
└─────────────┘
```

### Key Design Decisions

| Decision | Why |
|----------|-----|
| **Provider abstraction** | Swap Ollama / Gemini / Groq via `.env` — no code changes |
| **Chroma persistence** | Index survives restarts; no re-embedding every launch |
| **Separate read/admin API keys** | `/ask` is read-only; `/index` requires admin key |
| **Structured traces** | Debug bad answers via `trace_id` + retrieved chunks |
| **Eval suite** | Measure pass rate, citation accuracy, refusal behavior |

### Provider Modes

| Mode | LLM | Embeddings | Use Case |
|------|-----|------------|----------|
| Fully local | Ollama (`llama3.2:3b`) | Ollama (`nomic-embed-text`) | Privacy, no API cost |
| Hybrid | Groq (`llama-3.3-70b`) | Ollama (`nomic-embed-text`) | Fast cloud LLM + local search |
| Cloud | Gemini (`gemini-2.5-flash`) | Gemini (`gemini-embedding-2`) | Easiest setup, free tier |

---

## 4. Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Language | Python 3.11+ | Standard for AI/ML projects |
| RAG framework | LangChain | Document loaders, splitters, vector store integration |
| Vector DB | Chroma (persistent) | Embeddings survive restarts |
| LLM (local) | Ollama | Run open-source models locally |
| LLM (cloud) | Gemini, Groq | Free-tier APIs, fast inference |
| Embeddings | nomic-embed-text / Gemini | Convert text to searchable vectors |
| API | FastAPI | REST endpoints with auth middleware |
| Observability | Custom JSON tracer | `trace_id`, latency breakdown, chunk logging |
| Evaluation | Custom test runner | Keyword coverage, source hits, refusal checks |
| Config | python-dotenv | Environment-based provider switching |
| Container | Docker Compose | Optional Ollama service |

---

## 5. Project Structure (Current)

```
simpleAgent/
├── main.py                    # CLI (chat, index, info, eval)
├── README.md                  # Full documentation + architecture
├── LICENSE                    # MIT
├── requirements.txt
├── docker-compose.yml
├── .env.example
│
├── config/
│   ├── settings.py            # Load & validate .env (fail-fast on bad keys)
│   └── providers.py           # Factory: get_llm(), get_embeddings()
│
├── knowledge/
│   ├── loader.py              # Load .txt, .md, .pdf
│   └── indexer.py             # Chunk → embed → Chroma
│
├── assistant/
│   └── agent.py               # RAG pipeline + tracing
│
├── api/
│   ├── server.py              # FastAPI (/health, /ask, /index, /config)
│   └── auth.py                # Read/admin API key middleware
│
├── observability/
│   └── tracer.py              # Structured JSON traces
│
├── eval/
│   ├── test_cases.json        # 7 test Q&A pairs
│   ├── runner.py              # Scoring + pass rate report
│   └── results/               # Saved eval reports
│
├── data/documents/            # Knowledge base
├── chroma_db/                 # Persistent vector store
└── logs/                      # traces.jsonl + app.log
```

**Files worth highlighting in an interview:**
- `assistant/agent.py` — RAG pipeline, prompt template, citations, timing
- `config/providers.py` — factory pattern for swappable models
- `api/auth.py` — read vs admin API key separation
- `observability/tracer.py` — production debugging with `trace_id`
- `eval/runner.py` — automated quality measurement
- `config/settings.py` — fail-fast validation (catches placeholder API keys)

---

## 6. Core Features (What You've Built)

| Feature | Status | Interview value |
|---------|--------|-----------------|
| RAG with citations | Done | Grounded generation, not just chat |
| Multi-provider (Ollama/Gemini/Groq) | Done | Open-source + cloud flexibility |
| Persistent Chroma vector store | Done | Production-aware indexing |
| CLI + REST API | Done | Two interfaces |
| API authentication (read/admin) | Done | Security awareness |
| Observability (traces + latency) | Done | Debuggable in production |
| Evaluation suite (7 tests) | Done | Measurable quality (pass rate) |
| Config-driven design | Done | `.env` switching, no code changes |
| Document formats (.txt/.md/.pdf) | Done | Real document ingestion |
| Placeholder API key validation | Done | Defensive engineering |

---

## 7. How to Present This in an Interview

### Recommended flow (6–10 minutes)

#### Step 1: Problem (30 seconds)
> "Companies have internal docs but employees struggle to find answers. Generic LLMs hallucinate. I built a RAG assistant that retrieves relevant document chunks, generates grounded answers, and cites its sources."

#### Step 2: Architecture (2 minutes)
Walk through the 5-step RAG pipeline: Index → Retrieve → Augment → Generate → Cite.

Mention production additions:
- "API has read/admin key separation"
- "Every request logs a `trace_id` with retrieval vs generation latency"
- "I have an eval suite that scores pass rate on 7 test cases"

#### Step 3: Live demo (3 minutes)

```bash
python main.py info               # Show active providers (Ollama local mode)
python main.py index --rebuild    # Index documents
python main.py                    # Ask a question — show citations + trace
python main.py eval -v            # Show 7/7 pass rate
```

**Optional API demo:**
```bash
uvicorn api.server:app --reload
curl -H "X-API-Key: your-read-key" -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
# Point out trace_id, retrieval_ms, generation_ms in response
```

**Good demo questions:**
- "What model providers does this project support?"
- "How do I run fully local with Ollama?"
- "What are the three steps of RAG?"

#### Step 4: Code walkthrough (2 minutes)
Pick one based on interviewer interest:
- **RAG logic** → `assistant/agent.py` (`ask()` method)
- **Provider switching** → `config/providers.py`
- **Observability** → `observability/tracer.py`
- **Eval** → `eval/runner.py`

#### Step 5: Trade-offs & limitations (1 minute)
Be honest — see Section 10. Shows maturity.

---

## 8. Interview Q&A — RAG & Architecture

### "What is RAG and why did you use it?"
> RAG combines retrieval with generation. We search our documents first, pass relevant chunks as context, and ask the LLM to answer from that. This reduces hallucination and lets the system use private, up-to-date documents.

### "Why use an LLM at all? Why not just return search results?"
> Retrieval finds the right **chunks** — that's Chroma's job. The LLM **synthesizes** them into a natural answer. It handles paraphrased questions ("Can I upload PDFs?" vs "What file formats are supported?"), merges info across multiple chunks, and refuses when context is insufficient. A search-only script dumps raw text; the LLM explains it.

### "Is the output deterministic?"
> **No — not fully.** Retrieval is mostly stable (same question → same chunks). Generation is probabilistic — I use `temperature=0.2` for consistency. Citations are built deterministically from retrieved chunks in Python. For stricter reproducibility, I'd set `temperature=0`.

### "What type of prompting do you use?"
> **RAG-grounded zero-shot prompting.** A fixed template with: (1) role instruction, (2) guardrails ("answer only from context"), (3) retrieved chunks, (4) user question. No few-shot examples, no chain-of-thought, no tool-calling. The LLM only sees the top-K chunks retrieval selected — not the full knowledge base.

### "Why Chroma instead of in-memory storage?"
> In-memory stores lose data on restart. Chroma persists embeddings to disk — index once, query many times. In production I'd consider Qdrant or Pinecone for multi-tenant scale.

### "Why separate LLM and embedding providers?"
> They serve different jobs. Embeddings run at index time; the LLM runs per question. Hybrid mode (Ollama embeddings + Groq LLM) balances cost, privacy, and speed.

### "How do you prevent hallucination?"
> Four layers: (1) retrieve only relevant context, (2) prompt instructs "answer ONLY from context", (3) citations let users verify, (4) eval tests refusal on unknown questions.

### "What happens when you switch embedding providers?"
> Embeddings live in different vector spaces — not compatible. Must re-index: `python main.py index --rebuild`.

### "How would you scale this for production?"
> Already have: auth, tracing, eval. Next: async indexing queue, reranking, conversation memory, rate limiting, managed vector DB, Docker deploy with live demo URL.

### "What's the difference between this and a simple chatbot?"
> A chatbot uses only parametric LLM knowledge. This retrieves external knowledge at query time, grounds answers in documents, cites sources, and logs traces for debugging.

---

## 9. Interview Q&A — Models & Setup

### "Do I need `ollama pull`?"
> Only when `LLM_PROVIDER=ollama` or `EMBEDDING_PROVIDER=ollama`. Cloud-only mode (Gemini) needs no Ollama at all. `ollama pull` downloads models locally — like installing a dependency.

### "Can I use Hugging Face models instead of Ollama?"
> Yes, three ways: (1) **Via Ollama** — many Ollama models come from HF (`llama3.2`, `nomic-embed-text`), (2) **HF Inference API** — cloud, needs API key, (3) **transformers locally** — full control but needs more RAM/GPU. This project uses Ollama for local and Gemini/Groq for cloud — HF could be added as another provider.

### "Ollama vs Hugging Face — what's the difference?"
> Hugging Face = model library (where models live). Ollama = local runtime (downloads and runs them). Gemini/Groq = cloud runtime. Your `.env` picks which runtime to use.

### "Common setup mistake?"
> Placeholder API key in `.env` (`your-gemini-api-key-here`) while `EMBEDDING_PROVIDER=gemini`. The project now validates this at startup with a clear error message.

---

## 10. Interview Q&A — Python Concepts Used

Know these cold — interviewers often ask "walk me through your code":

| Concept | Where in project | One-liner |
|---------|------------------|-----------|
| **Modules & packages** | `config/`, `knowledge/`, `api/` | Organized code, not one giant file |
| **Classes & OOP** | `EnterpriseKnowledgeAssistant` | Blueprint with state (`self.llm`) + methods (`ask()`) |
| **Dataclasses** | `Settings`, `Citation`, `RequestTrace` | Typed data containers without boilerplate |
| **Type hints** | `str \| None`, `list[str]`, `-> Settings` | Documents expected types |
| **Factory pattern** | `get_llm()`, `get_embeddings()` | Creates right model from config |
| **Dependency injection** | Pass `Settings` into classes | Testable, swappable components |
| **`pathlib.Path`** | File loading, config paths | Modern file path handling |
| **`os.getenv` + dotenv** | `config/settings.py` | Config without hardcoded secrets |
| **Exception handling** | `raise ValueError`, `try/except` | Fail fast with clear errors |
| **`argparse`** | `main.py` subcommands | CLI with `chat`, `index`, `eval` |
| **FastAPI + Depends** | `api/auth.py` | API key middleware on endpoints |
| **Logging** | `observability/tracer.py` | Structured traces, not just `print()` |

**Study order:** `config/settings.py` → `config/providers.py` → `assistant/agent.py` → `api/auth.py` → `eval/runner.py`

---

## 11. Deep Dive Q&A — Detailed Answers

These are the most common technical questions interviewers ask about this project. Study these thoroughly.

---

### Q1. Which chunking strategy is used here and why?

**What we use:**

| Setting | Default | Config key |
|---------|---------|------------|
| Splitter | `RecursiveCharacterTextSplitter` (LangChain) | — |
| Chunk size | 500 characters | `CHUNK_SIZE` |
| Chunk overlap | 50 characters | `CHUNK_OVERLAP` |
| Top-K retrieved | 4 chunks | `TOP_K` |

**Code location:** `knowledge/indexer.py`

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=self.settings.chunk_size,
    chunk_overlap=self.settings.chunk_overlap,
)
chunks = splitter.split_documents(docs)
```

**How RecursiveCharacterTextSplitter works:**

It tries to split text on natural boundaries in this order:
1. Paragraph breaks (`\n\n`)
2. Single newlines (`\n`)
3. Spaces
4. Characters (last resort)

So it avoids cutting mid-sentence when possible — unlike a naive fixed-size split every 500 chars.

**Why this strategy?**

| Reason | Explanation |
|--------|-------------|
| **Documents are longer than LLM context per chunk** | A full PDF or markdown file can't fit in one retrieval unit. Splitting makes search precise. |
| **500 chars is a practical default** | Small enough to retrieve specific facts; large enough to keep sentence context. For your sample `company_knowledge.md`, 1 file → ~4 chunks. |
| **50-char overlap** | Prevents losing context at chunk boundaries. If a sentence spans two chunks, overlap ensures at least one chunk contains the full thought. |
| **Recursive splitting** | Respects document structure (paragraphs, lines) better than arbitrary character cuts. |

**Chunking trade-offs:**

| Chunk size | Pros | Cons |
|------------|------|------|
| **Small (200)** | Precise retrieval | Loses broader context |
| **Medium (500)** — our default | Balanced | May split related ideas |
| **Large (1500+)** | More context per chunk | Retrieves irrelevant text, wastes LLM context window |

**What we did NOT use (and why):**

| Strategy | Why not (yet) |
|----------|---------------|
| **Semantic chunking** | Splits by meaning boundaries — better quality but slower and more complex |
| **Document-structure chunking** | Splits by markdown headers — good for structured docs, not implemented |
| **Fixed token-based splitting** | More accurate for LLM limits, but char-based is simpler for a portfolio v1 |

**Interview answer:**
> "I use RecursiveCharacterTextSplitter with 500-character chunks and 50-character overlap. It splits on natural boundaries like paragraphs and newlines, which keeps sentences intact. Overlap prevents losing context at boundaries. These values are configurable via CHUNK_SIZE and CHUNK_OVERLAP in .env."

---

### Q2. What embedding model is used and why?

**What we use (configurable via `.env`):**

| Provider | Model | When |
|----------|-------|------|
| **Ollama (local)** | `nomic-embed-text` | `EMBEDDING_PROVIDER=ollama` |
| **Gemini (cloud)** | `models/gemini-embedding-2` | `EMBEDDING_PROVIDER=gemini` |

**Code location:** `config/providers.py` → `get_embeddings()`

**What embeddings do:**

They convert text into a **vector** (list of numbers) that captures semantic meaning. Similar meanings → similar vectors → findable via cosine similarity in Chroma.

```
"What is RAG?"        → [0.12, -0.34, 0.56, ...]
"Explain retrieval"   → [0.11, -0.31, 0.54, ...]  ← close in vector space
"Company revenue"     → [0.89, 0.22, -0.67, ...]  ← far away
```

**Why `nomic-embed-text` (local)?**

| Reason | Detail |
|--------|--------|
| Open-source | Free, runs locally via Ollama, no API cost |
| Purpose-built for retrieval | Trained specifically for embedding/search tasks |
| Small & fast | ~274 MB — runs on a laptop |
| Good quality | Widely used in RAG tutorials and production prototypes |
| Privacy | Document text never leaves your machine during embedding |

**Why `gemini-embedding-2` (cloud)?**

| Reason | Detail |
|--------|--------|
| Easy setup | No Ollama required — just an API key |
| Strong quality | Google's latest embedding model |
| Same vendor as LLM | Convenient when using Gemini for both embedding and generation |
| Free tier | Good for demos and development |

**Critical rule:**
> You must use the **same embedding model** for indexing and querying. If you switch `EMBEDDING_PROVIDER`, you must re-index (`python main.py index --rebuild`) because vectors from different models live in incompatible spaces.

**Interview answer:**
> "For local mode I use nomic-embed-text via Ollama — it's open-source, lightweight, and designed for retrieval. For cloud mode I use Gemini's embedding-2 model. Embeddings convert text to vectors so we can find semantically similar chunks, not just keyword matches. Switching embedding models requires a full re-index."

---

### Q3. What vector database is used and why?

**What we use:** **Chroma** (persistent, local)

**Code location:** `knowledge/indexer.py`

```python
Chroma(
    collection_name=self.settings.chroma_collection,  # "enterprise_knowledge"
    embedding_function=self.embeddings,
    persist_directory=str(self.settings.chroma_dir),  # chroma_db/
)
```

**What Chroma stores:**

For each document chunk:
- The original text
- Its embedding vector (from nomic-embed-text or Gemini)
- Metadata (source file path)

**Why Chroma?**

| Reason | Explanation |
|--------|-------------|
| **Persistent** | Index survives app restarts — stored in `chroma_db/` on disk |
| **Simple setup** | No separate server to run — embedded library |
| **LangChain integration** | Works natively with `langchain-chroma` |
| **Free & open-source** | No cloud account needed for portfolio/dev |
| **Good for prototyping** | Fast to set up, sufficient for single-user / demo scale |

**How search works at query time:**

```python
vector_store.similarity_search_with_score(question, k=TOP_K)
```

1. Embed the user's question with the same embedding model
2. Compare question vector to all stored chunk vectors (cosine similarity)
3. Return top-K most similar chunks with relevance scores

**Alternatives considered:**

| Database | Pros | Cons | When to use |
|----------|------|------|-------------|
| **Chroma** — ours | Simple, persistent, local | Not ideal for multi-tenant production scale | Portfolio, prototypes, single team |
| **In-memory** (early version) | Fastest setup | Lost on restart | Learning only |
| **FAISS** | Very fast search | No built-in persistence/metadata | Research, large static indexes |
| **Qdrant** | Production-ready, filtering | Needs Docker/server | Production deployments |
| **Pinecone** | Fully managed, scalable | Paid, cloud-only | Enterprise SaaS products |

**Interview answer:**
> "I use Chroma as a persistent local vector store. It saves embeddings to disk in chroma_db/, integrates cleanly with LangChain, and requires no separate server. For a portfolio project it's the right balance of simplicity and production awareness. At scale I'd move to Qdrant or Pinecone for multi-tenant isolation and managed infrastructure."

---

### Q4. Why is semantic search used? What other search options exist? What are the trade-offs?

**What this project uses:** **Semantic (vector) search** via embedding similarity.

**Why semantic search?**

Users ask questions in **natural language**, which rarely matches document wording exactly.

| User question | Document text | Keyword search | Semantic search |
|---------------|---------------|----------------|-----------------|
| "How do I run locally?" | "Fully local (open-source, private)" | May miss — no word "locally" | Finds it — understands meaning |
| "What file types work?" | "Supported formats: .txt, .md, .pdf" | Needs exact words | Understands "file types" ≈ "formats" |
| "Explain the three steps" | "RETRIEVAL - AUGMENTATION - GENERATION" | Misses if phrasing differs | Matches conceptually |

Semantic search embeds both the question and documents into the same vector space, so **meaning similarity** drives retrieval — not exact word matching.

**Other search methods available:**

### A. Keyword search (BM25 / TF-IDF)

```text
How it works: Counts word overlap between query and documents
Example:     "Ollama setup" matches docs containing "Ollama" and "setup"
```

| Pros | Cons |
|------|------|
| Fast, no ML model needed | Misses paraphrases and synonyms |
| Exact term matching (good for IDs, codes) | "car" won't match "automobile" |
| Deterministic | Poor for natural language questions |

### B. Semantic search (what we use)

```text
How it works: Embed query + docs as vectors, find nearest neighbors
Example:     "How to run offline?" matches "fully local" chunk
```

| Pros | Cons |
|------|------|
| Understands meaning and paraphrases | Needs embedding model (cost/latency) |
| Works with natural language | Can miss exact keyword matches (SKU codes, IDs) |
| Better for Q&A over prose docs | Vectors must be re-built when embedding model changes |

### C. Hybrid search (semantic + keyword)

```text
How it works: Run both BM25 and vector search, merge/rerank results
Example:     Best of both — "error code E404" (keyword) + "how to fix login" (semantic)
```

| Pros | Cons |
|------|------|
| Best retrieval quality in production | More complex to implement |
| Handles both exact terms and meaning | Two indexes to maintain |

### D. Metadata / filtered search

```text
How it works: Filter by file type, date, department BEFORE vector search
Example:     "Search only HR docs from 2024"
```

Not implemented in this project — single collection, no filters.

**Trade-off summary:**

| Method | Best for | Used here? |
|--------|----------|------------|
| Keyword (BM25) | Exact terms, codes, SKUs | No |
| Semantic (vector) | Natural language Q&A | **Yes** |
| Hybrid | Production RAG systems | No (future) |
| Full-text (SQL LIKE) | Simple apps | No |

**Interview answer:**
> "I use semantic search because users ask questions in natural language that won't exactly match document wording. Embeddings capture meaning, so 'run locally' matches 'fully local open-source mode'. The trade-off is it needs an embedding model and can miss exact keyword matches — which is why production systems often use hybrid search combining BM25 and vectors. That's a planned improvement."

---

### Q5. What is evaluation and what does it tell about this project?

**What evaluation is:**

A structured test suite that runs predefined questions against the assistant and **scores the answers automatically** — like unit tests for your RAG pipeline.

**Code location:** `eval/runner.py`, `eval/test_cases.json`

**How to run:**
```bash
python main.py eval        # summary
python main.py eval -v       # per-question details
```

**What it measures:**

| Metric | What it checks | Pass criteria |
|--------|----------------|---------------|
| **Keyword coverage** | Expected terms appear in the answer | ≥ 60% of keywords found |
| **Source hit** | Correct document was cited | Expected file in citations |
| **Refusal check** | Unknown questions are declined safely | Answer contains refusal phrases |
| **Latency** | Response time per question | Informational (not pass/fail) |
| **Pass rate** | Overall % of tests passed | e.g. 7/7 = 100% |

**Example test case:**
```json
{
  "id": "rag_definition",
  "question": "What is RAG?",
  "expected_keywords": ["retrieval", "augment", "generation"],
  "expected_source_contains": "company_knowledge.md",
  "must_refuse": false
}
```

**What eval tells about this project:**

| Insight | What it proves |
|---------|----------------|
| **Retrieval works** | Source hit = correct chunks are being found |
| **Generation works** | Keyword coverage = LLM answers with expected facts |
| **Guardrails work** | Refusal test = system doesn't hallucinate on unknown questions |
| **Regression safety** | Change chunk size or model → re-run eval → catch breakage |
| **Measurable quality** | "100% pass rate" is a concrete resume/interview metric |

**What eval does NOT measure (limitations):**

| Gap | Better approach |
|-----|-----------------|
| Answer phrasing quality | LLM-as-judge |
| Factual faithfulness to chunk | RAGAS faithfulness score |
| Retrieval precision@K | Manual labeling of correct chunks |
| Edge cases | Expand test suite to 50+ cases |

**Results saved to:** `eval/results/latest.json`

**Interview answer:**
> "I built an eval suite with 7 test cases covering factual Q&A and refusal behavior. It scores keyword coverage, citation accuracy, and whether the system correctly declines unknown questions. It gives me a pass rate I can quote — currently 100% on my knowledge base — and acts as a regression test when I change chunk size or swap models."

---

### Q6. What is the use of observability?

**What observability is:**

The ability to **see inside the system** when something goes wrong — what was retrieved, how long each step took, which model was used.

**Code location:** `observability/tracer.py`

**What gets logged per request:**

| Field | Purpose |
|-------|---------|
| `trace_id` | Unique ID to correlate API response with logs |
| `retrieval_ms` | How long vector search took |
| `generation_ms` | How long LLM inference took |
| `total_ms` | End-to-end latency |
| `chunks` | Which document chunks were retrieved (source, score, excerpt) |
| `cited_sources` | Which files appeared in citations |
| `provider_info` | Which LLM and embedding model were active |

**Where logs are written:**

```
logs/
├── traces.jsonl    # One JSON object per line — machine-readable
└── app.log         # Human-readable summary
```

**Why observability matters in RAG:**

RAG has **two failure modes** — retrieval can fail OR generation can fail. Without traces, you can't tell which.

| Symptom | Diagnosis via traces |
|---------|---------------------|
| Wrong answer | Check `chunks` — were the right passages retrieved? |
| Slow response | Compare `retrieval_ms` vs `generation_ms` — which step is the bottleneck? |
| Hallucination | Check if retrieved chunks actually contain the claimed fact |
| Inconsistent answers | Same `trace_id` pattern — compare chunk scores across runs |

**Example debug workflow:**

1. User reports bad answer
2. Copy `trace_id` from API response (e.g. `b01711e1`)
3. Search `logs/traces.jsonl` for that ID
4. Inspect retrieved chunks and scores
5. Fix: tune `TOP_K`, chunk size, or prompt — not blind guessing

**Interview answer:**
> "Every ask and index request logs a structured trace with trace_id, retrieval latency, generation latency, and the exact chunks retrieved. If an answer is wrong, I can look up the trace and immediately see whether retrieval failed — wrong chunks — or generation failed — LLM ignored context. This is essential for debugging RAG in production."

---

### Q7. How do you know if a response is correct or not?

There is **no single perfect method** — this project uses **multiple layers** of verification:

### Layer 1: Citations (user-facing verification)

Every answer includes **source file + relevance score**:

```
Sources:
  [1] data/documents/company_knowledge.md (relevance: 0.54)
```

The user (or you) can open the source file and verify the answer matches the text.

**Limitation:** Citation proves *which doc was used*, not that the LLM interpreted it correctly.

---

### Layer 2: Prompt guardrails (prevention)

The prompt instructs the LLM:

```
Answer using ONLY the context below.
Do not invent facts not present in the context.
If context is insufficient, say so clearly.
```

This reduces but does not eliminate hallucination.

---

### Layer 3: Automated evaluation (systematic testing)

`python main.py eval` runs 7 test cases:

| Test type | Validates |
|-----------|-----------|
| Factual Q&A (6 tests) | Expected keywords present + correct source cited |
| Refusal (1 test) | Unknown question → "I don't have that information" |

Pass rate = measurable quality metric.

---

### Layer 4: Observability (debugging incorrect answers)

When an answer looks wrong:
1. Check `trace_id` in response
2. Read `logs/traces.jsonl`
3. Verify retrieved chunks actually support the answer

---

### Layer 5: Manual review (gold standard)

For production, you would add:
- Human-labeled Q&A dataset (ground truth answers)
- LLM-as-judge ("Is this answer supported by the context?")
- RAGAS metrics: faithfulness, answer relevance, context precision

**Not implemented yet** — eval uses keyword matching, which is simpler but less nuanced.

### Correctness checklist for this project:

| Method | Automated? | What it catches |
|--------|------------|-----------------|
| Citations | Yes | Wrong source document |
| Keyword eval | Yes | Missing key facts in answer |
| Refusal eval | Yes | Hallucination on unknown questions |
| Trace inspection | Manual | Retrieval vs generation failures |
| Human review | Manual | Subtle factual errors, tone issues |
| LLM-as-judge | Not yet | Semantic correctness |

**Interview answer:**
> "I use a layered approach: citations let users verify sources, prompt guardrails reduce hallucination, and an automated eval suite tests keyword coverage and refusal behavior with a measurable pass rate. For debugging, trace logs show exactly which chunks were retrieved. For production I'd add LLM-as-judge and a larger labeled dataset — keyword matching is a good start but not sufficient alone."

---

### Q8. What are the limitations of this project?

Be proactive about these in interviews — it shows engineering maturity.

### RAG & Retrieval limitations

| Limitation | Impact | Future fix |
|------------|--------|------------|
| **No reranking** | Raw similarity search can return noisy chunks | Add cross-encoder reranker after retrieval |
| **Fixed chunk size (500 chars)** | May split related ideas or include irrelevant text | Tune per document type; try semantic chunking |
| **Top-K = 4 only** | May miss relevant chunks ranked 5th+ | Increase K + rerank; hybrid search |
| **Single vector collection** | All docs in one index — no per-team isolation | Multi-collection with metadata filters |
| **Manual re-indexing** | New documents require `index --rebuild` | File watcher or upload API with auto-index |
| **Embedding model lock-in** | Switching models requires full re-index | Document embedding versioning |

### LLM & Generation limitations

| Limitation | Impact | Future fix |
|------------|--------|------------|
| **Not fully deterministic** | `temperature=0.2` — answers vary slightly between runs | Set `temperature=0` for strict reproducibility |
| **LLM can still hallucinate** | Prompt guardrails reduce but don't eliminate it | Stronger eval + LLM-as-judge |
| **No conversation memory** | Each question is independent — no follow-ups | Session history in prompt |
| **Small local model (llama3.2:3b)** | Lower quality than larger models | Swap to qwen2.5:7b or cloud Groq/Gemini |

### Production & Scale limitations

| Limitation | Impact | Future fix |
|------------|--------|------------|
| **Synchronous API** | Indexing blocks the request thread | Background job queue (Celery/RQ) |
| **No rate limiting** | API can be overwhelmed | slowapi or nginx rate limits |
| **Chroma local only** | Doesn't scale to millions of docs or multi-user | Qdrant / Pinecone |
| **No document upload API** | Must manually drop files in `data/documents/` | `POST /upload` endpoint |
| **Eval suite is small (7 tests)** | Keyword matching is simplistic | Expand to 50+ cases + RAGAS metrics |
| **No deployed demo URL** | Interviewer can't try it live | Docker deploy on Render/Fly.io |

### Security limitations

| Limitation | Impact | Future fix |
|------------|--------|------------|
| **API keys in `.env`** | Fine for dev; not for production secret management | Vault / AWS Secrets Manager |
| **No HTTPS** | Local dev only | TLS termination via nginx or cloud provider |
| **No input sanitization** | Prompt injection possible | Input length limits + injection detection |

**How to frame in interview:**
> "This is a solid v1 that demonstrates RAG, provider abstraction, auth, tracing, and evals. The main gaps are reranking for better retrieval, conversation memory for follow-ups, a larger eval dataset with LLM-as-judge, and a deployed demo. I'm aware of the trade-offs and have a clear roadmap for v2."

---

## 12. Current Limitations (Quick Checklist)

See **Section 11, Q8** for detailed explanations. Summary:

- [x] Evaluation framework
- [x] API authentication
- [x] Observability / tracing
- [ ] No conversation memory
- [ ] Manual re-indexing only
- [ ] No reranking
- [ ] Single collection (no multi-tenant)
- [ ] Not fully deterministic (`temperature=0.2`)
- [ ] Small eval suite (keyword-based only)
- [ ] No live deployed demo

---

## 13. Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| High | Evaluation suite | Done — `python main.py eval` |
| High | API authentication | Done — read/admin keys |
| High | Observability / tracing | Done — `logs/traces.jsonl` |
| Medium | Conversation memory | Planned |
| Medium | Reranking (cross-encoder) | Planned |
| Medium | Document upload API | Planned |
| Medium | Expand eval to 20+ test cases | Planned |
| Low | Langfuse integration | Planned |
| Low | Web UI (Streamlit / Next.js) | Planned |
| Low | Docker full-stack deploy + live URL | Planned |

---

## 14. Resume Bullet Points

- Built a **RAG-based Enterprise Knowledge Assistant** in Python (LangChain, Chroma, FastAPI) that answers questions from internal documents with **source citations** and automated **evaluation** (7/7 pass rate)
- Designed a **provider abstraction layer** supporting local open-source models (Ollama/Llama) and cloud APIs (Gemini/Groq) via environment-based configuration
- Implemented **API authentication** (read/admin key separation), **structured observability** (`trace_id`, retrieval/generation latency), and persistent vector indexing for `.txt`, `.md`, `.pdf` documents
- Exposed the assistant via **CLI and REST API** with fail-fast config validation and JSON trace logging for production debugging

---

## 15. Pre-Interview Checklist

- [ ] Ollama running if using local mode (`ollama list`)
- [ ] `.env` configured (no placeholder API keys)
- [ ] `python main.py index --rebuild` completed
- [ ] `python main.py eval` shows high pass rate
- [ ] Test 2–3 chat questions — citations + trace appear
- [ ] Know which file to open for code walkthrough
- [ ] Can draw RAG pipeline on whiteboard (5 steps)
- [ ] Can explain why LLM is needed beyond search
- [ ] Can explain prompting type (RAG-grounded zero-shot)
- [ ] Optional: API demo with `X-API-Key` header ready

---

## 16. 30-Second Elevator Pitch

> "I built an Enterprise Knowledge Assistant — a production-style RAG system that answers questions from company documents with citations. It uses LangChain and Chroma for retrieval, supports local open-source models via Ollama and cloud APIs via Gemini and Groq, and includes API authentication, structured tracing with latency breakdown, and an automated eval suite. The architecture separates indexing, retrieval, and generation, and it's exposed through both a CLI and a secured FastAPI REST API."

---

## 17. Quick Command Reference

```bash
# Setup
cp .env.example .env
pip install -r requirements.txt
ollama pull llama3.2:3b && ollama pull nomic-embed-text   # local mode only

# Run
python main.py info
python main.py index --rebuild
python main.py                    # chat
python main.py eval -v            # evaluation

# API
uvicorn api.server:app --reload
curl -H "X-API-Key: YOUR_KEY" -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" -d '{"question": "What is RAG?"}'

# Debug
grep "trace_id_here" logs/traces.jsonl   # find full retrieval log
```

---

*Last updated: August 2026*
