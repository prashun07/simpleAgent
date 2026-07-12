# My Simple AI Agent Project

A basic AI agent designed to respond to simple queries.

## Setup

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd simpleAgent
   ```

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the API key:
   - Create a `.env` file in the project root.
   - Add your Gemini API key:

   ```env
   GEMINI_API_KEY="your-api-key"
   ```

## How to Run

```bash
python main.py
```

## Features

- Responds to greetings such as "hello"
- Answers simple questions like "time" and "who are you"
- Loads a response from a real LLM


## Future Enhancements

- Implement memory for conversational context