from agent import SimpleAIAgent
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return

    agent = SimpleAIAgent(api_key=api_key)
    print("Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = agent.process_input(user_input)
        print(f"Agent: {response}")

if __name__ == "__main__":
    main()