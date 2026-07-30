"""
Enterprise Knowledge Assistant — CLI entry point.

Usage:
  python main.py              # interactive chat
  python main.py index        # index documents into Chroma
  python main.py index --rebuild   # wipe and re-index
  python main.py info         # show active model providers
"""

import argparse
import sys
from pathlib import Path

from assistant.agent import EnterpriseKnowledgeAssistant
from config.settings import load_settings, validate_settings


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Knowledge Assistant — RAG with local or cloud models"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("chat", help="Start interactive chat (default)")
    index_parser = subparsers.add_parser("index", help="Index documents into Chroma")
    index_parser.add_argument(
        "--rebuild", action="store_true", help="Delete existing index and rebuild"
    )
    subparsers.add_parser("info", help="Show active LLM and embedding providers")

    args = parser.parse_args()
    command = args.command or "chat"

    if command == "info":
        _show_info()
        return

    try:
        assistant = EnterpriseKnowledgeAssistant()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    if command == "index":
        result = assistant.index(force_rebuild=args.rebuild)
        print(result["message"])
        return

    _run_chat(assistant)


def _show_info():
    settings = load_settings()
    try:
        validate_settings(settings)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    from config.providers import describe_active_models

    info = describe_active_models(settings)
    print("\n=== Enterprise Knowledge Assistant ===")
    print(f"  Mode:       {info['mode']}")
    print(f"  LLM:        {info['llm_provider']} / {info['llm_model']}")
    print(f"  Embeddings: {info['embedding_provider']} / {info['embedding_model']}")
    print(f"  Documents:  {settings.documents_dir}")
    print(f"  Vector DB:  {settings.chroma_dir}")
    print()


def _run_chat(assistant: EnterpriseKnowledgeAssistant):
    info = assistant.provider_info
    print("\n=== Enterprise Knowledge Assistant ===")
    print(f"  LLM:        {info['llm_provider']} / {info['llm_model']}")
    print(f"  Embeddings: {info['embedding_provider']} / {info['embedding_model']}")
    print(f"  Mode:       {info['mode']}")
    print("\nIndexing documents...")
    index_result = assistant.index()
    print(index_result["message"])
    print("\nReady. Ask questions about your knowledge base.")
    print("Commands: 'exit' to quit, 'reindex' to refresh documents\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        if user_input.lower() == "reindex":
            result = assistant.index(force_rebuild=True)
            print(result["message"])
            continue

        response = assistant.ask(user_input)
        _save_response(response.format())
        print(f"\nAssistant:\n{response.format()}\n")


def _save_response(text: str):
    try:
        output_path = Path(__file__).resolve().parent / "data" / "result.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    main()
