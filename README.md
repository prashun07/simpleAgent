```markdown
# My Simple AI Agent Project

A basic AI agent designed to respond to simple queries.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd my_simple_ai_agent_project
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure API Key (if needed):**
    *   Create a `.env` file in the root directory.
    *   Add your OpenAI API key (or similar) to it:
        ```
        OPENAI_API_KEY="sk-your-actual-api-key"
        ```

## How to Run

```bash
python main.py
```

## Features

*   Responds to "hello", "time", "who are you".
*   Loads a simple knowledge base from `data/knowledge.txt`.

## Future Enhancements

*   Integrate with a real LLM (e.g., OpenAI, Anthropic).
*   Add more sophisticated tool use.
*   Implement memory for conversational context.
```