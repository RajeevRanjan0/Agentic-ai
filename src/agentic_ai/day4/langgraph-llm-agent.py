from langgraph.graph import START, END, StateGraph
from typing import TypedDict
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

# result = llm.invoke("What is the capital of France?")

# print(result.content)

def invoke_llm(state):
    prompt = state['prompt']
    response = llm.invoke(prompt)
    state['response'] = response.content
    return state

graph_groq = StateGraph(dict)
graph_groq.add_node("invoke_llm", invoke_llm)

graph_groq.add_edge(START, "invoke_llm")
graph_groq.add_edge("invoke_llm", END)

graph_state = graph_groq.compile()

prompt = "What is the capital of France?"

result = graph_state.invoke({'prompt': prompt})

print("Response from LLM:", result['response'])

