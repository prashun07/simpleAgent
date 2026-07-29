# Simple RAG Agent

A beginner-friendly **RAG (Retrieval-Augmented Generation)** agent built with Python, LangChain, and Google Gemini.

## What is RAG?

A normal LLM only knows what it was trained on. **RAG** lets it answer questions about **your** documents by:

1. **Retrieval** — Search your documents for chunks related to the question
2. **Augmentation** — Add those chunks to the prompt as context
3. **Generation** — Ask the LLM to answer using that context

```
  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
  │ Your docs   │────▶│ Vector store │◀────│  Embeddings │
  │ (data/*.txt)│     │  (in-memory) │     │   (Gemini)  │
  └─────────────┘     └──────┬───────┘     └─────────────┘
                             │
  User question ──▶ RETRIEVE relevant chunks
                             │
                             ▼
                    AUGMENT prompt with context
                             │
                             ▼
                    GENERATE answer (Gemini LLM)
```

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point — starts the chat loop |
| `rag_agent.py` | RAG pipeline (retrieve → augment → generate) |
| `tool/langchainloader.py` | Loads docs, splits chunks, builds vector index |
| `data/knowledge.txt` | Sample knowledge base (add your own `.txt` files here) |
| `agent.py` | Original simple agent (no RAG) — kept for comparison |
| `.env` | Your `GEMINI_API_KEY` (never commit this) |

## Setup

1. Clone and enter the project:

   ```bash
   git clone <your-repo-url>
   cd simpleAgent
   ```

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

5. Create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY="your-api-key-here"
   ```

## How to Run

```bash
python main.py
```

On startup the agent indexes all `.txt` files in `data/`, then you can ask questions.

### Example questions

- "What is RAG and how does it work?"
- "What files are in this project?"
- "Which Gemini models does this project use?"

Type `exit` to quit.

## How It Works (Step by Step)

### 1. Indexing (happens once at startup)

Defined in `tool/langchainloader.py`:

- Load `.txt` files from `data/`
- Split text into ~500-character chunks (with overlap so sentences aren't cut awkwardly)
- Convert each chunk to a **vector** (embedding) using `models/gemini-embedding-2`
- Store vectors in an in-memory search index

### 2. Retrieval (per question)

Defined in `rag_agent.py` → `_retrieve()`:

- Your question is also embedded
- The index finds the **3 most similar** chunks (cosine similarity)

### 3. Augmentation (per question)

Defined in `rag_agent.py` → `_build_prompt()`:

- Retrieved chunks are inserted into a prompt template
- The LLM is instructed to answer **only** from that context

### 4. Generation (per question)

Defined in `rag_agent.py` → `process_input()`:

- The augmented prompt is sent to `gemini-2.5-flash`
- The model returns an answer grounded in your documents

## Adding Your Own Knowledge

1. Add any `.txt` file to the `data/` folder
2. Restart `python main.py` (re-indexing happens on startup)
3. Ask questions about your new content

> `data/result.txt` is ignored — it's only used to save the last agent response.

## Models Used

| Role | Model | Why |
|------|-------|-----|
| Embeddings | `models/gemini-embedding-2` | Converts text to vectors for search |
| Chat / Generation | `gemini-2.5-flash` | Fast, capable LLM for answers |

Both use the same `GEMINI_API_KEY` from Google AI Studio (free tier available).

## Compare: RAG vs Simple Agent

| | `agent.py` (Simple) | `rag_agent.py` (RAG) |
|---|---|---|
| Knowledge source | One static file, barely used | Searched dynamically per question |
| LLM context | Just your question | Question + relevant document chunks |
| Best for | Greetings, demos | Q&A over your own documents |

Run the original agent by changing the import in `main.py` from `RAGAgent` to `SimpleAgent`.

## Next Steps (when you're ready)

- Add more documents to `data/`
- Tune `chunk_size` and `TOP_K` in the code
- Try a persistent vector DB (Chroma, FAISS) instead of in-memory
- Add conversation memory so follow-up questions work
