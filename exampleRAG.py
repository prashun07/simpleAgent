from deepagents import create_deep_agent
from langchain.messages import HumanMessage

EXAMPLE_QUERY= " How do i create RAG based simple agents using langchain?"

baseline_agent = create_deep_agent(
    model="google_genai:gemini-3.5-flash",
    system_prompt="Tell me about gemini history briefly",
)

result = baseline_agent.invoke(
    {"messages":[HumanMessage(content=EXAMPLE_QUERY)]}
)

print(result["message"][-1].text)