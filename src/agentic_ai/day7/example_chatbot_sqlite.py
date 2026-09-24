from langgraph.graph import START, END, StateGraph
import ollama
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver

class ChatBotState(TypedDict):
    user_message : str
    chat_history : list[dict]
    reply : str

def chatbot(state: ChatBotState):
    history = state.get("chat_history", []) + [{"role": "user", "content": state['user_message']}]
    response = ollama.chat(model="gpt-oss:120b-cloud", messages=history)
    reply = response['message']['content']
    history += [{"role": "assistant", "content": reply}]
    state['reply'] = reply
    state['chat_history'] = history
    return state

graph_builder = StateGraph(ChatBotState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Same thread_id every run -> SqliteSaver reloads chat_history even after a restart,
# because the checkpoint is written to a database file on disk, not to process memory.
settings = {"configurable": {"thread_id": "user-1"}}

with SqliteSaver.from_conn_string("Persistence/day7_chatbot_memory.db") as sqlite_memory:
    graph = graph_builder.compile(checkpointer=sqlite_memory)
    print("Chatbot ready (in-memory chat). Type 'bye' or 'quit' to stop.")
    while True:
        user_message = input("You: ").lower().strip()
        if user_message in ['bye', 'quit', 'end']:
            print("Chatbot: Goodbye!")
            break;
        prompt = {"user_message": user_message}
        result = graph.invoke(prompt, config=settings)
        print(f"chatbot : {result['reply']}")