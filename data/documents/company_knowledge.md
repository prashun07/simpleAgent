# Enterprise Knowledge Assistant - Knowledge Base

This folder holds documents the assistant can search and answer from.
Supported formats: .txt, .md, .pdf

## What is RAG?

RAG (Retrieval-Augmented Generation) combines:
1. RETRIEVAL - find relevant document chunks using embeddings
2. AUGMENTATION - add those chunks to the LLM prompt
3. GENERATION - the LLM answers using your company knowledge

## Supported Model Modes

### Fully local (open-source, private, no API cost)
Set in .env:
  LLM_PROVIDER=ollama
  EMBEDDING_PROVIDER=ollama

Pull models first:
  ollama pull llama3.2:3b
  ollama pull nomic-embed-text

### Cloud with open-source models (Groq hosts Llama)
  LLM_PROVIDER=groq
  EMBEDDING_PROVIDER=ollama   # or gemini for cloud embeddings

### Cloud Gemini (easy free tier)
  LLM_PROVIDER=gemini
  EMBEDDING_PROVIDER=gemini

## Example Questions

- What model providers does this project support?
- How do I run fully local with Ollama?
- What file formats can I add to the knowledge base?
- Explain the three steps of RAG

## Adding Documents

1. Drop .txt, .md, or .pdf files into data/documents/
2. Run: python main.py index --rebuild
3. Ask questions via: python main.py

## Project Architecture

  data/documents/  -->  Knowledge Loader  -->  Text Splitter
                                                    |
                                                    v
  User Question  -->  Chroma Vector DB  <--  Embeddings (Ollama/Gemini)
                           |
                           v
                    LLM (Ollama/Gemini/Groq)  -->  Answer + Citations
