from langgraph.graph import START, END, StateGraph
from typing import TypedDict
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import sys
import ollama

load_dotenv()

# llm = ChatOllama(model="lama3:latest")

class State(TypedDict):
    user_message : str
    chat_history : list[dict]
    reply : str

def chatgpt(state: State):
    history = state.get("chat_history", []) + [{"role": "user", "content" : state['user_message']}]
    prompt = state['user_message']
    # reply = llm.invoke(prompt, message=history)
    response = ollama.chat(model="gpt-oss:120b-cloud", messages=history)
    reply = response["message"]["content"]
    history = history + [{"role" : "assistant", "content": reply}]
    state['chat_history'] = history
    state['reply'] = reply
    return {"chat_history": history, "reply" : reply}

graph = StateGraph(State)

graph.add_node("chatgpt", chatgpt)
graph.add_edge(START, "chatgpt")
graph.add_edge("chatgpt", END)

workflow = graph.compile()
print("Chat GPT started...")
while True:
    print("Please enter bye or quit for stopping the chat...")
    user_message = input("Please enter your question/thoughts: ").lower().strip()
    if user_message in ['bye', 'quit']:
        break;
    prompt = {"user_message": user_message}
    result = workflow.invoke(prompt)
    # print(f"Result : {result}")
    print("Chatbot:", result["reply"])
