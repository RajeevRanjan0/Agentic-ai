from langgraph.graph import START, END, StateGraph
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")

class State(TypedDict):
    question: str
    action: str
    answer: str

def decide_Answer(state: State):
    question = state['question']

    prompt = f"""Choose the next action from IT request Question.
    return only TOOL for password request.
    return only ANSWER for all other questions.
    Question: {question}"""

    llm_response = llm.invoke(prompt)
    print(f"llm_response: {llm_response}")
    action = llm_response.content.strip().upper()
    print(f"action: {action}")
    if action not in ["TOOL", "ANSWER"]:
        action = "ANSWER"

    state['action'] = action
    return state

def next_node(state: State):
    return state["action"]

def tool_node(state: State):
    state['answer'] = f"Tool result: open the password reset page."
    return state

def tool_answer(state: State):
    state['action'] = f"Direct answer: your request was received"
    return state

graph = StateGraph(State)
graph.add_node("decide", decide_Answer)
graph.add_node("tool", tool_node)
graph.add_node("answer", tool_answer)

graph.add_edge(START, "decide")
graph.add_conditional_edges("decide", next_node)
graph.add_edge("tool", END)
graph.add_edge("answer", END)

workflow_State = graph.compile()

result = workflow_State.invoke({"question": "can i reset my password?"})

print(result)