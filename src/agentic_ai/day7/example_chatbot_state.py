from langgraph.graph import START, END, StateGraph
import ollama
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver

class ChatState(TypedDict):
    user_message : str
    chat_history : list[dict]
    reply : str

def chatbot(state: ChatState):
    history = state.get("chat_history", []) + [{"role" : "user", "content": state['user_message']}]
    llm_response = ollama.chat(model="gpt-oss:120b-cloud", messages=history)
    reply = llm_response["message"]["content"]
    history += [{"role": "assistant", "content": reply}]
    state['chat_history'] = history
    state['reply'] = reply

    return state

graph_builder = StateGraph(ChatState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile(checkpointer=InMemorySaver())


# Same thread_id on every call -> the checkpointer reloads chat_history each time.
settings = {"configurable" : {"thread_id": "student-1"}}

print("Chatbot ready (in-memory chat). Type 'bye' or 'quit' to stop.")
while True:
    user_message = input("You: ").lower().strip()
    if user_message in ['bye', 'quit', 'end']:
        print("Chatbot: Goodbye!")
        break;
    prompt = {"user_message": user_message}
    result = graph.invoke(prompt, config=settings)
    print(f"chatbot : {result['reply']}")