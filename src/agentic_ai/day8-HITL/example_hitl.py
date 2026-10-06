from langgraph.graph import START, END, StateGraph
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict
from langchain_ollama import ChatOllama
import ollama
from langgraph.types import Command, interrupt

class chatbot_history(TypedDict):
    user_message : str
    chat_history : list[dict]
    reply : str
    approval : bool
    approval_action : str

def chatbot(state: chatbot_history):
    if state['approval_action'] == "ACTION CANCELLED":
        state['reply'] = "ACTION CANCELLED, so no further processing"
        return state
    history = state.get('chat_history', []) + [{"role": "user", "content": state["user_message"]}]
    print("chat initated....")
    llm_response = ollama.chat(model="llama3:latest", messages=history)
    print("chat end and got response...")
    reply = llm_response['message']['content']
    history  += [{"role": "assistant", "content": reply}]
    state['reply'] = reply
    state['chat_history'] = history
    return state

def ask_approval(chatbot_history):
    ask = interrupt("Please approve for procced further as yes/no: ")
    chatbot_history['approval'] = ask
    return chatbot_history

def finish(chatbot_history):
    if chatbot_history["approval"]:
        message = "ACTION APPROVED"
    else: 
        message = "ACTION CANCELLED"
    chatbot_history['approval_action'] = message
    return {"approval_action": message}

graph_builder = StateGraph(chatbot_history)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("ask_approval", ask_approval)
graph_builder.add_node("finish", finish)

# graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge(START, "ask_approval")
graph_builder.add_edge("ask_approval", "finish")
graph_builder.add_edge("finish", "chatbot")
graph_builder.add_edge("chatbot", END)

connection = sqlite3.connect("STATE_MEMORY/chatbot_history.db", check_same_thread=False)
checkpointer = SqliteSaver(connection)
print("compiling the graph...")
graph = graph_builder.compile(checkpointer=checkpointer)
print("graph compiled successfully...")

settings = {"configurable": {"thread_id": "student-2"}}

if __name__ == "__main__":
    # approval_action = input("approve the llm call (yes/no) : ")
    # result = graph.invoke(Command(resume=(approval_action.lower()=="yes")), config=settings)
    # print("Approval action:", result)
    # import sys
    # if result['approval_action'] == "ACTION CANCELLED":
    #     print("ACTION CANCELLED, so no further processing")
    #     sys.exit(0)
    
    print("Invoking the graph with user message...")
    question = input("Enter your question for the chatbot : ")
    response = graph.invoke({"user_message": question}, config=settings)
    print("Response:", response)
    # print("Chat history:", response['chat_history']) 

    approval_action = input("approve the llm call (yes/no) : ")
    result = graph.invoke(Command(resume=(approval_action.lower()=="yes")), config=settings)
    print("\n\nApproval action:", result)
    print("\n\nchat reply: ", result['reply'])
