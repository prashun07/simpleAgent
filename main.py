from pathlib import Path

import os
from dotenv import load_dotenv

from rag_agent import RAGAgent

load_dotenv()  # Load variables from .env


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return

    print("Building RAG index from data/ ...")
    agent = RAGAgent(api_key=api_key)

    print("\nRAG Agent is ready. Ask questions about your knowledge base.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Your prompt: ")
        if user_input.lower() == "exit":
            break
        response = agent.process_input(user_input)
        _save_response(response)
        print(f"\nAgent: {response}\n")


def _save_response(response):
    try:
        output_path = Path(__file__).resolve().parent / "data" / "result.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(response) + "\n", encoding="utf-8")
        return str(output_path)
    except OSError as exc:
        return f"Unable to save, {exc}"


if __name__ == "__main__":
    main()
