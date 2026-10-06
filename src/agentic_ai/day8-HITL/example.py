from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

def ask_approval(state):
    approved = interrupt("Please approve to proceed further as yes/no: ")
    state['approved'] = approved
    return {"approved": approved}

def finish(state):
    # message = "Action completed." if state["approved"] else "Action cancelled."
    if state.get("approved"):
        message = "Action completed."
    else:
        message = "Action cancelled."
    return {"message": message}


graph_builder = StateGraph(dict)
graph_builder.add_node("ask_approval", ask_approval)    
graph_builder.add_node("finish", finish)  

graph_builder.add_edge(START, "ask_approval")
graph_builder.add_edge("ask_approval", "finish")
graph_builder.add_edge("finish", END)

graph = graph_builder.compile(checkpointer=InMemorySaver())

settings = {"configurable": {"thread_id": "student-2"}}
result = graph.invoke({"action": "Reset the account"}, config=settings)
print("result : ", result)


answer = input("Please approve to proceed further as yes/no: ")
result = graph.invoke(Command(resume=(answer.lower()=="yes")), config=settings)
print("Approval action:", result["message"])
print("result:", result)

# question = "Please approve to proceed further as yes/no: "
# graph.invoke({"message": question}, config=settings)
