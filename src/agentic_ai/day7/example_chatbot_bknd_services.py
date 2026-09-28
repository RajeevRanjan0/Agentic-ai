from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict
import ollama
import sqlite3

class Chatbot_history(TypedDict):
    user_message : str
    chat_history : list[dict]
    reply : str

Ollama_model_list = ["gpt-oss:120b-cloud", "llama3:latest"]
DEFAULT_MODEL = "llama3:latest"

def extract_chat_content(state):
    # 1. Check if user_message exists and is not empty
    user_msg = state.get('user_message')
    if not user_msg:
        return "No user message found.", None
        
    history = state.get('chat_history', [])
    assistant_msg = None
    
    # 2. Loop backwards to find where this specific user_message exists in history
    # We look for a 'user' role with matching content, then grab the subsequent 'assistant' role.
    for i in range(len(history) - 1, -1, -1):
        turn = history[i]
        
        if turn.get('role') == 'user' and turn.get('content') == user_msg:
            # Check if there is a next message in history and if it belongs to the assistant
            if i + 1 < len(history) and history[i + 1].get('role') == 'assistant':
                assistant_msg = history[i + 1].get('content')
                break # Successfully found the matching pair!

    return user_msg, assistant_msg


def chatbot_old(state: Chatbot_history):
    user_msg, assistant_msg = extract_chat_content(state=state)
    if user_msg and assistant_msg:
        print(f"cache output: {user_msg}, {assistant_msg}")
        return state
    history = state.get('chat_history', []) + [{"role" : "user", "content": state["user_message"]}]
    llm_response = ollama.chat(model=Ollama_model_list[1] , messages=history)
    reply = llm_response['message']['content']
    history  += [{"role" : "assistant", "content": reply}]
    state['reply'] = reply
    state['chat_history'] = history
    return state

def chatbot(state: Chatbot_history, config: dict | None = None):
    configurable = (config or {}).get("configurable", {})
    selected_model = configurable.get("model", DEFAULT_MODEL)

    if selected_model not in Ollama_model_list:
        raise ValueError(
            f"Unsupported model {selected_model!r}. "
            f"Choose from: {', '.join(Ollama_model_list)}"
        )

    history = list(state.get("chat_history", []))
    history.append({"role": "user", "content": state["user_message"]})

    llm_response = ollama.chat(model=selected_model, messages=history)
    reply = llm_response["message"]["content"]

    history.append({"role": "assistant", "content": reply})
    return {
        **state,
        "reply": reply,
        "chat_history": history,
    }

agent_builder = StateGraph(Chatbot_history)
agent_builder.add_node("chatbot", chatbot)
agent_builder.add_edge(START, "chatbot")
agent_builder.add_edge("chatbot", END)



connection = sqlite3.connect("Persistence/my_chatbot_memory.db", check_same_thread=False)
checkpointer = SqliteSaver(connection)
graph = agent_builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    settings = {"configurable": {"thread_id": "student-1"}}
    prompt = {"user_message": "what's the capital of US?"}
    response = graph.invoke(prompt, config=settings)
    print("chat_history : ", response['chat_history'])
    print("len of chat_history : ", len(response['chat_history']))

    print("final reply: ", response['reply'])