from google import genai
from config import GEMINI_API_KEY

# prompt = input("Enter the prompt you want to give(keep it short pls):")


# client = genai.Client(api_key=GEMINI_API_KEY) 
# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents=prompt
# )

# print(response.text)

class SimpleAIAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.knowledge_base = self._load_knowledge("data/knowledge.txt")
        print(f"Agent initialized with API Key: {'*' * len(api_key)}")

    def _load_knowledge(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "No external knowledge base loaded."

    def process_input(self, user_input):
        # Simple rule-based processing for demonstration
        if "hello" in user_input.lower():
            return "Hello there! How can I help you today?"
        elif "knowledge" in user_input.lower():
            return f"My current knowledge base contains: {self.knowledge_base[:50]}..." # show first 50 chars
        elif "time" in user_input.lower():
            import datetime
            return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}."
        elif "who are you" in user_input.lower():
            return "I am a simple AI agent designed to assist you."
        else:
            # In a real agent, you'd send this to an LLM
            return f"I received your input: '{user_input}'. I'm still learning how to respond to that."