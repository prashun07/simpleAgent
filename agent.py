from google import genai



class SimpleAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.knowledge_base = self._load_knowledge("data/knowledge.txt")

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
            return "I am a simple AI agent designed by Prashun Kumar to assist you."
        else:
            # In a real agent, you'd send this to an LLM
            response = self.call_llm(user_input)
            return response.text
        
    def call_llm(self, user_input):
        client = genai.Client(api_key=self.api_key) 
        response = client.models.generate_content(model="gemini-2.5-flash", contents=user_input) 
        return response

        